"""Exact-money helpers for allocating and simplifying trip debts."""

import heapq
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
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

    # Max-heaps (via negated amounts). Ties break on the lowest user id so the
    # output is deterministic and identical to the previous O(n^2) selection.
    debtors = [(balance, user_id) for user_id, balance in net_cents.items() if balance < 0]
    creditors = [(-balance, user_id) for user_id, balance in net_cents.items() if balance > 0]
    heapq.heapify(debtors)
    heapq.heapify(creditors)

    simplified: list[DebtTransaction] = []
    while debtors and creditors:
        debt_cents, debtor_id = heapq.heappop(debtors)  # most negative first
        negative_credit_cents, creditor_id = heapq.heappop(creditors)
        credit_cents = -negative_credit_cents
        payment_cents = min(-debt_cents, credit_cents)

        simplified.append(
            DebtTransaction(
                debtor_id=debtor_id,
                creditor_id=creditor_id,
                amount=_from_cents(payment_cents),
            )
        )
        if debt_cents + payment_cents < 0:
            heapq.heappush(debtors, (debt_cents + payment_cents, debtor_id))
        if credit_cents - payment_cents > 0:
            heapq.heappush(creditors, (-(credit_cents - payment_cents), creditor_id))

    return simplified


def split_by_percentage(
    total_amount: MoneyAmount,
    percentages: Sequence[tuple[int, MoneyAmount]],
) -> dict[int, Decimal]:
    """Split by percentages (max two decimals) that must add up to exactly 100.

    Shares are floored to the cent, then leftover cents go to the participants with
    the largest fractional remainders (ties: earlier participant first). This is the
    same rule the web and Android clients use.
    """
    total_cents = _to_cents(total_amount)
    if total_cents < 0:
        raise ValueError("total_amount cannot be negative")
    if not percentages:
        raise ValueError("at least one participant is required")
    user_ids = [user_id for user_id, _ in percentages]
    if len(set(user_ids)) != len(user_ids):
        raise ValueError("participant_ids must be unique")

    basis_points = [_to_cents(percent) for _, percent in percentages]  # hundredths of a percent
    if any(points < 0 or points > 10_000 for points in basis_points):
        raise ValueError("percentages must be between 0 and 100")
    if sum(basis_points) != 10_000:
        raise ValueError("percentages must add up to 100")

    floors = [total_cents * points // 10_000 for points in basis_points]
    remainders = [total_cents * points % 10_000 for points in basis_points]
    leftover = total_cents - sum(floors)
    recipients = sorted(range(len(user_ids)), key=lambda index: (-remainders[index], index))[:leftover]
    bonus = set(recipients)
    return {
        user_id: _from_cents(floors[index] + (index in bonus))
        for index, user_id in enumerate(user_ids)
    }


def split_exact(
    total_amount: MoneyAmount,
    amounts: Sequence[tuple[int, MoneyAmount]],
) -> dict[int, Decimal]:
    """Validate explicit per-person amounts: unique users, none negative, sum == total."""
    total_cents = _to_cents(total_amount)
    if total_cents < 0:
        raise ValueError("total_amount cannot be negative")
    if not amounts:
        raise ValueError("at least one participant is required")
    user_ids = [user_id for user_id, _ in amounts]
    if len(set(user_ids)) != len(user_ids):
        raise ValueError("participant_ids must be unique")

    share_cents = [_to_cents(amount) for _, amount in amounts]
    if any(cents < 0 for cents in share_cents):
        raise ValueError("shares cannot be negative")
    if sum(share_cents) != total_cents:
        raise ValueError("exact shares must add up to the total")
    return {user_id: _from_cents(cents) for user_id, cents in zip(user_ids, share_cents)}


def net_balances(
    expenses: Iterable[tuple[int, MoneyAmount, Mapping[int, MoneyAmount]]],
) -> dict[int, Decimal]:
    """Net position per user from ``(payer_id, total_amount, {user_id: amount_owed})``.

    Positive means the user is owed money; negative means they owe. Every expense
    must have shares that add up to its total, so balances always sum to zero.
    """
    net_cents: dict[int, int] = defaultdict(int)
    for payer_id, total_amount, shares in expenses:
        total_cents = _to_cents(total_amount)
        share_cents = {user_id: _to_cents(amount) for user_id, amount in shares.items()}
        if sum(share_cents.values()) != total_cents:
            raise ValueError("expense shares must add up to the total")
        net_cents[payer_id] += total_cents
        for user_id, cents in share_cents.items():
            net_cents[user_id] -= cents
    return {user_id: _from_cents(cents) for user_id, cents in net_cents.items()}
