"""Exact-money helpers for allocating and simplifying trip debts."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Union

MoneyAmount = Union[Decimal, int, str]
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


@dataclass(frozen=True)
class DebtTransaction:
    """A payment from one user to another, expressed in major currency units."""

    debtor_id: int
    creditor_id: int
    amount: Decimal


def _to_cents(amount: MoneyAmount) -> int:
    if isinstance(amount, (bool, float)):
        raise TypeError("amount must be a Decimal, integer, or decimal string")

    try:
        decimal_amount = amount if isinstance(amount, Decimal) else Decimal(amount)
        if not decimal_amount.is_finite():
            raise ValueError("amount must be finite")
        rounded_amount = decimal_amount.quantize(_CENT)
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("amount must be a valid value with at most two decimal places") from error

    if rounded_amount != decimal_amount:
        raise ValueError("amount must have at most two decimal places")
    return int(rounded_amount * _HUNDRED)


def _from_cents(amount: int) -> Decimal:
    return (Decimal(amount) / _HUNDRED).quantize(_CENT)


def split_equally(
    total_amount: MoneyAmount, participant_ids: Sequence[int]
) -> dict[int, Decimal]:
    """Allocate an amount in cents, giving leftover cents to earlier participants."""
    total_cents = _to_cents(total_amount)
    if total_cents < 0:
        raise ValueError("total_amount cannot be negative")
    if not participant_ids:
        raise ValueError("at least one participant is required")
    if len(set(participant_ids)) != len(participant_ids):
        raise ValueError("participant_ids must be unique")

    base_cents, remainder = divmod(total_cents, len(participant_ids))
    return {
        participant_id: _from_cents(base_cents + (index < remainder))
        for index, participant_id in enumerate(participant_ids)
    }


def simplify_debts(
    transactions: Iterable[DebtTransaction],
) -> list[DebtTransaction]:
    """Net debts and greedily settle the largest debtor against the largest creditor."""
    net_cents: dict[int, int] = defaultdict(int)
    for transaction in transactions:
        amount_cents = _to_cents(transaction.amount)
        if amount_cents <= 0:
            raise ValueError("debt transaction amounts must be positive")
        if transaction.debtor_id == transaction.creditor_id:
            raise ValueError("a user cannot owe themselves")

        net_cents[transaction.debtor_id] -= amount_cents
        net_cents[transaction.creditor_id] += amount_cents

    simplified: list[DebtTransaction] = []
    while True:
        debtors = [
            (user_id, balance)
            for user_id, balance in net_cents.items()
            if balance < 0
        ]
        creditors = [
            (user_id, balance)
            for user_id, balance in net_cents.items()
            if balance > 0
        ]
        if not debtors:
            break

        debtor_id, debt_cents = min(debtors, key=lambda item: (item[1], item[0]))
        creditor_id, credit_cents = min(
            creditors, key=lambda item: (-item[1], item[0])
        )
        payment_cents = min(-debt_cents, credit_cents)

        simplified.append(
            DebtTransaction(
                debtor_id=debtor_id,
                creditor_id=creditor_id,
                amount=_from_cents(payment_cents),
            )
        )
        net_cents[debtor_id] += payment_cents
        net_cents[creditor_id] -= payment_cents

    return simplified
