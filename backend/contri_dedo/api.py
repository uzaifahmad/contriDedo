from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .debt_simplifier import DebtTransaction, net_balances, simplify_debts, split_by_percentage, split_equally, split_exact
from .models import Base, Expense, ExpenseSplit, IdempotencyKey, LoginSession, Trip, TripMember, User

_bearer = HTTPBearer(auto_error=False)
_SESSION_DAYS = 30


class AuthInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=120)


class UserOutput(BaseModel):
    id: int
    email: str
    display_name: str


class AuthOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOutput


class TripInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    destination: str = Field(default="", max_length=200)


class MemberInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class SplitInput(BaseModel):
    user_id: int
    amount_owed: str
    calculation_method: str
    percentage: str | None = None


class ExpenseInput(BaseModel):
    description: str = Field(min_length=1, max_length=240)
    total_amount: str
    payer_id: int
    splits: list[SplitInput] = Field(min_length=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    category: str = Field(default="Other", min_length=1, max_length=40)


class ExpenseOutput(BaseModel):
    id: int
    description: str
    total_amount: str
    payer_id: int
    currency: str
    category: str
    created_at: datetime
    splits: list[dict[str, int | str]]


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}:{digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    salt_hex, digest_hex = encoded.split(":", maxsplit=1)
    candidate = _password_hash(password, bytes.fromhex(salt_hex)).split(":", maxsplit=1)[1]
    return hmac.compare_digest(candidate, digest_hex)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _user_output(user: User) -> UserOutput:
    return UserOutput(id=user.id, email=user.email, display_name=user.display_name)


def _require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Sign in is required.")
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == _token_hash(credentials.credentials)))
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at if session and session.expires_at.tzinfo else (session.expires_at.replace(tzinfo=timezone.utc) if session else now)
    if session is None or expires_at <= now:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")
    return user


def _member_trip(db: Session, trip_id: int, user_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    membership = db.scalar(select(TripMember.id).where(TripMember.trip_id == trip_id, TripMember.user_id == user_id))
    if trip is None or membership is None:
        raise HTTPException(status_code=404, detail="Trip not found.")
    return trip


def _expense_output(db: Session, expense: Expense) -> ExpenseOutput:
    splits = db.scalars(select(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id)).all()
    return ExpenseOutput(
        id=expense.id,
        description=expense.description,
        total_amount=f"{expense.total_amount:.2f}",
        payer_id=expense.payer_id,
        currency=expense.currency,
        category=expense.category,
        created_at=expense.created_at,
        splits=[{"user_id": row.user_id, "amount_owed": f"{row.amount_owed:.2f}", "calculation_method": row.calculation_method} for row in splits],
    )


def create_app(database_url: str | None = None, create_tables: bool = False) -> FastAPI:
    app = FastAPI(title="contriDedo API", version="1.0.0")
    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Idempotency-Key"],
    )
    if database_url is not None:
        from sqlalchemy import create_engine, event
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        is_sqlite = database_url.startswith("sqlite")
        test_engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if is_sqlite else {},
            poolclass=StaticPool if is_sqlite and database_url.endswith("://") else None,
        )
        if is_sqlite:
            @event.listens_for(test_engine, "connect")
            def enable_sqlite_foreign_keys(connection, _record):
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        factory = sessionmaker(bind=test_engine, expire_on_commit=False)
        app.state.engine = test_engine
        app.state.session_factory = factory

        def override_get_db():
            yield from _yield_session(factory)

        app.dependency_overrides[get_db] = override_get_db
        if create_tables:
            Base.metadata.create_all(test_engine)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth/sign-up", response_model=AuthOutput, status_code=201)
    def sign_up(body: AuthInput, db: Session = Depends(get_db)) -> AuthOutput:
        email = body.email.strip().lower()
        if "@" not in email:
            raise HTTPException(status_code=422, detail="Enter a valid email address.")
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        user = User(email=email, display_name=(body.display_name or email.split("@", 1)[0]).strip(), password_hash=_password_hash(body.password))
        db.add(user)
        db.flush()
        token = secrets.token_urlsafe(32)
        db.add(LoginSession(user_id=user.id, token_hash=_token_hash(token), expires_at=datetime.now(timezone.utc) + timedelta(days=_SESSION_DAYS)))
        db.commit()
        return AuthOutput(access_token=token, user=_user_output(user))

    @app.post("/api/auth/sign-in", response_model=AuthOutput)
    def sign_in(body: AuthInput, db: Session = Depends(get_db)) -> AuthOutput:
        user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
        if user is None or not _verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        token = secrets.token_urlsafe(32)
        db.add(LoginSession(user_id=user.id, token_hash=_token_hash(token), expires_at=datetime.now(timezone.utc) + timedelta(days=_SESSION_DAYS)))
        db.commit()
        return AuthOutput(access_token=token, user=_user_output(user))

    @app.get("/api/auth/me", response_model=UserOutput)
    def me(user: User = Depends(_require_user)) -> UserOutput:
        return _user_output(user)

    @app.post("/api/trips", status_code=201)
    def create_trip(body: TripInput, db: Session = Depends(get_db), user: User = Depends(_require_user)) -> dict[str, object]:
        trip = Trip(name=body.name.strip(), destination=body.destination.strip(), created_by=user.id)
        db.add(trip)
        db.flush()
        db.add(TripMember(trip_id=trip.id, user_id=user.id))
        db.commit()
        return _trip_output(db, trip)

    @app.get("/api/trips")
    def list_trips(db: Session = Depends(get_db), user: User = Depends(_require_user)) -> list[dict[str, object]]:
        trips = db.scalars(select(Trip).join(TripMember).where(TripMember.user_id == user.id).order_by(Trip.id)).all()
        return [_trip_output(db, trip) for trip in trips]

    @app.get("/api/trips/{trip_id}")
    def get_trip(trip_id: int, db: Session = Depends(get_db), user: User = Depends(_require_user)) -> dict[str, object]:
        trip = _member_trip(db, trip_id, user.id)
        return _trip_output(db, trip, include_expenses=True)

    @app.post("/api/trips/{trip_id}/members", status_code=201)
    def add_member(trip_id: int, body: MemberInput, db: Session = Depends(get_db), user: User = Depends(_require_user)) -> UserOutput:
        _member_trip(db, trip_id, user.id)
        member = db.scalar(select(User).where(User.email == body.email.strip().lower()))
        if member is None:
            raise HTTPException(status_code=404, detail="No account exists for this email yet.")
        exists = db.scalar(select(TripMember.id).where(TripMember.trip_id == trip_id, TripMember.user_id == member.id))
        if exists is None:
            db.add(TripMember(trip_id=trip_id, user_id=member.id))
            db.commit()
        return _user_output(member)

    @app.post("/api/trips/{trip_id}/expenses", response_model=ExpenseOutput, status_code=201)
    def create_expense(
        trip_id: int,
        body: ExpenseInput,
        db: Session = Depends(get_db),
        user: User = Depends(_require_user),
        idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key", max_length=200),
    ) -> ExpenseOutput:
        _member_trip(db, trip_id, user.id)
        normalized = {"trip_id": trip_id, "body": body.model_dump(mode="json")}
        request_hash = hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if idempotency_key:
            previous = db.scalar(select(IdempotencyKey).where(IdempotencyKey.user_id == user.id, IdempotencyKey.key == idempotency_key))
            if previous is not None:
                if previous.request_hash != request_hash:
                    raise HTTPException(status_code=422, detail="Idempotency key was already used with a different request.")
                saved = db.get(Expense, previous.expense_id)
                if saved is not None:
                    return _expense_output(db, saved)

        member_ids = set(db.scalars(select(TripMember.user_id).where(TripMember.trip_id == trip_id)).all())
        participant_ids = [split.user_id for split in body.splits]
        if body.payer_id not in member_ids or any(member_id not in member_ids for member_id in participant_ids):
            raise HTTPException(status_code=422, detail="Payer and split participants must belong to this trip.")
        methods = {split.calculation_method for split in body.splits}
        if len(methods) != 1 or not methods <= {"equal", "percentage", "exact"}:
            raise HTTPException(status_code=422, detail="Use one supported split method for all participants.")
        try:
            total = Decimal(body.total_amount)
            supplied = [(split.user_id, split.amount_owed) for split in body.splits]
            shares = split_exact(total, supplied)
            method = next(iter(methods))
            if method == "equal" and split_equally(total, participant_ids) != shares:
                raise ValueError("Equal shares do not match the canonical cent allocation.")
            if method == "percentage":
                supplied_percentages = [split.percentage for split in body.splits]
                if any(value is not None for value in supplied_percentages):
                    if not all(value is not None for value in supplied_percentages):
                        raise ValueError("Provide a percentage for every split participant.")
                    percentages = [(split.user_id, split.percentage) for split in body.splits if split.percentage is not None]
                    if split_by_percentage(total, percentages) != shares:
                        raise ValueError("Percentage shares do not match the canonical cent allocation.")
        except (ValueError, TypeError, ArithmeticError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if total <= 0:
            raise HTTPException(status_code=422, detail="Expense total must be greater than zero.")

        expense = Expense(trip_id=trip_id, payer_id=body.payer_id, total_amount=total, description=body.description.strip(), currency=body.currency.upper(), category=body.category.strip())
        db.add(expense)
        db.flush()
        db.add_all([ExpenseSplit(trip_id=trip_id, expense_id=expense.id, user_id=member_id, amount_owed=amount, calculation_method=method) for member_id, amount in shares.items()])
        if idempotency_key:
            db.add(IdempotencyKey(user_id=user.id, key=idempotency_key, request_hash=request_hash, expense_id=expense.id))
        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise HTTPException(status_code=409, detail="Expense could not be saved; retry with the same idempotency key.") from error
        db.refresh(expense)
        return _expense_output(db, expense)

    @app.get("/api/trips/{trip_id}/expenses", response_model=list[ExpenseOutput])
    def list_expenses(trip_id: int, db: Session = Depends(get_db), user: User = Depends(_require_user)) -> list[ExpenseOutput]:
        _member_trip(db, trip_id, user.id)
        expenses = db.scalars(select(Expense).where(Expense.trip_id == trip_id, Expense.deleted_at.is_(None)).order_by(Expense.created_at, Expense.id)).all()
        return [_expense_output(db, expense) for expense in expenses]

    @app.get("/api/trips/{trip_id}/balances")
    def get_balances(trip_id: int, db: Session = Depends(get_db), user: User = Depends(_require_user)) -> dict[str, object]:
        _member_trip(db, trip_id, user.id)
        expenses = db.scalars(select(Expense).where(Expense.trip_id == trip_id, Expense.deleted_at.is_(None))).all()
        ledger_by_currency: dict[str, list[tuple[int, Decimal, dict[int, Decimal]]]] = {}
        debts_by_currency: dict[str, list[DebtTransaction]] = {}
        for expense in expenses:
            rows = db.scalars(select(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id)).all()
            shares = {row.user_id: Decimal(row.amount_owed) for row in rows}
            ledger_by_currency.setdefault(expense.currency, []).append((expense.payer_id, Decimal(expense.total_amount), shares))
            debts_by_currency.setdefault(expense.currency, []).extend(
                DebtTransaction(member_id, expense.payer_id, amount)
                for member_id, amount in shares.items()
                if member_id != expense.payer_id and amount > 0
            )
        users = {member.id: member for member in db.scalars(select(User).join(TripMember).where(TripMember.trip_id == trip_id)).all()}
        balance_rows = []
        simplified_rows = []
        for currency, ledger in sorted(ledger_by_currency.items()):
            balances = net_balances(ledger)
            balance_rows.extend(
                {"user_id": member_id, "display_name": users[member_id].display_name, "balance": f"{amount:.2f}", "currency": currency}
                for member_id, amount in sorted(balances.items())
            )
            simplified_rows.extend(
                {"debtor_id": item.debtor_id, "creditor_id": item.creditor_id, "amount": f"{item.amount:.2f}", "currency": currency}
                for item in simplify_debts(debts_by_currency[currency])
            )
        return {
            "balances": balance_rows,
            "simplified_debts": simplified_rows,
        }

    return app


def _yield_session(factory):
    db = factory()
    try:
        yield db
    finally:
        db.close()


def _trip_output(db: Session, trip: Trip, include_expenses: bool = False) -> dict[str, object]:
    members = db.scalars(select(User).join(TripMember).where(TripMember.trip_id == trip.id).order_by(User.id)).all()
    expenses = db.scalars(select(Expense).where(Expense.trip_id == trip.id, Expense.deleted_at.is_(None)).order_by(Expense.created_at, Expense.id)).all()
    spent_by_currency: dict[str, Decimal] = {}
    for expense in expenses:
        spent_by_currency[expense.currency] = spent_by_currency.get(expense.currency, Decimal("0.00")) + Decimal(expense.total_amount)
    result: dict[str, object] = {
        "id": trip.id,
        "name": trip.name,
        "destination": trip.destination,
        "created_at": trip.created_at,
        "total_spent_by_currency": {currency: f"{amount:.2f}" for currency, amount in sorted(spent_by_currency.items())},
        "member_count": len(members),
        "members": [_user_output(member).model_dump() for member in members],
    }
    if include_expenses:
        result["expenses"] = [_expense_output(db, expense).model_dump(mode="json") for expense in expenses]
    return result


app = create_app()