import unittest
from decimal import Decimal

from contri_dedo.debt_simplifier import (
    DebtTransaction,
    simplify_debts,
    split_equally,
)


class SplitEquallyTests(unittest.TestCase):
    def test_distributes_remainder_cents_without_losing_value(self) -> None:
        shares = split_equally(Decimal("10.00"), [1, 2, 3])

        self.assertEqual(
            shares,
            {
                1: Decimal("3.34"),
                2: Decimal("3.33"),
                3: Decimal("3.33"),
            },
        )
        self.assertEqual(sum(shares.values()), Decimal("10.00"))


class SimplifyDebtsTests(unittest.TestCase):
    def test_collapses_debt_chain_into_direct_payment(self) -> None:
        simplified = simplify_debts(
            [
                DebtTransaction(1, 2, Decimal("10.00")),
                DebtTransaction(2, 3, Decimal("10.00")),
            ]
        )

        self.assertEqual(
            simplified,
            [DebtTransaction(1, 3, Decimal("10.00"))],
        )

    def test_returns_no_payments_when_debts_cancel(self) -> None:
        simplified = simplify_debts(
            [
                DebtTransaction(1, 2, Decimal("4.25")),
                DebtTransaction(2, 1, Decimal("4.25")),
            ]
        )

        self.assertEqual(simplified, [])

    def test_rejects_float_amounts(self) -> None:
        with self.assertRaises(TypeError):
            simplify_debts([DebtTransaction(1, 2, 0.1)])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
