import random
import unittest
from collections import defaultdict
from decimal import Decimal

from contri_dedo.debt_simplifier import (
    DebtTransaction,
    net_balances,
    simplify_debts,
    split_by_percentage,
    split_equally,
    split_exact,
)


def _reference_simplify(transactions):
    """The original O(n^2) selection, kept to prove the heap version is equivalent."""
    net = defaultdict(int)
    for t in transactions:
        cents = int(t.amount * 100)
        net[t.debtor_id] -= cents
        net[t.creditor_id] += cents
    out = []
    while True:
        debtors = [(u, b) for u, b in net.items() if b < 0]
        creditors = [(u, b) for u, b in net.items() if b > 0]
        if not debtors:
            break
        d_id, d_bal = min(debtors, key=lambda item: (item[1], item[0]))
        c_id, c_bal = min(creditors, key=lambda item: (-item[1], item[0]))
        pay = min(-d_bal, c_bal)
        out.append(DebtTransaction(d_id, c_id, Decimal(pay) / 100))
        net[d_id] += pay
        net[c_id] -= pay
    return out


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


    def test_heap_version_matches_reference_on_random_ledgers(self) -> None:
        rng = random.Random(20261010)
        for _ in range(300):
            users = rng.randint(2, 12)
            transactions = []
            for _ in range(rng.randint(1, 40)):
                debtor, creditor = rng.sample(range(1, users + 1), 2)
                amount = Decimal(rng.randint(1, 50_000)) / 100
                transactions.append(DebtTransaction(debtor, creditor, amount))
            self.assertEqual(simplify_debts(transactions), _reference_simplify(transactions))

    def test_never_needs_more_than_n_minus_one_payments(self) -> None:
        rng = random.Random(7)
        for _ in range(100):
            users = rng.randint(2, 15)
            transactions = [
                DebtTransaction(*rng.sample(range(1, users + 1), 2), Decimal(rng.randint(1, 9_999)) / 100)
                for _ in range(rng.randint(1, 60))
            ]
            self.assertLessEqual(len(simplify_debts(transactions)), users - 1)

    def test_handles_large_groups(self) -> None:
        transactions = [DebtTransaction(i, i + 1, Decimal("1.00")) for i in range(1, 5000)]
        self.assertEqual(simplify_debts(transactions), [DebtTransaction(1, 5000, Decimal("1.00"))])


class SplitByPercentageTests(unittest.TestCase):
    def test_matches_client_remainder_rule(self) -> None:
        shares = split_by_percentage(
            "10.00", [(101, "33.34"), (102, "33.33"), (103, "33.33")]
        )
        self.assertEqual(
            shares, {101: Decimal("3.34"), 102: Decimal("3.33"), 103: Decimal("3.33")}
        )

    def test_remainder_goes_to_largest_fraction_then_earlier_participant(self) -> None:
        shares = split_by_percentage("0.05", [(1, "50"), (2, "50")])
        self.assertEqual(shares, {1: Decimal("0.03"), 2: Decimal("0.02")})
        self.assertEqual(sum(shares.values()), Decimal("0.05"))

    def test_shares_always_sum_to_total(self) -> None:
        rng = random.Random(3)
        for _ in range(200):
            parts = rng.randint(1, 6)
            cuts = sorted(rng.randint(0, 10_000) for _ in range(parts - 1))
            points = [b - a for a, b in zip([0, *cuts], [*cuts, 10_000])]
            percentages = [(i + 1, Decimal(p) / 100) for i, p in enumerate(points)]
            total = Decimal(rng.randint(1, 1_000_000)) / 100
            self.assertEqual(sum(split_by_percentage(total, percentages).values()), total)

    def test_rejects_bad_percentages(self) -> None:
        with self.assertRaises(ValueError):
            split_by_percentage("10.00", [(1, "60"), (2, "30")])
        with self.assertRaises(ValueError):
            split_by_percentage("10.00", [(1, "101"), (2, "-1")])
        with self.assertRaises(ValueError):
            split_by_percentage("10.00", [(1, "50"), (1, "50")])


class SplitExactTests(unittest.TestCase):
    def test_accepts_amounts_that_add_up(self) -> None:
        self.assertEqual(
            split_exact("10.00", [(1, "2.50"), (2, "7.50")]),
            {1: Decimal("2.50"), 2: Decimal("7.50")},
        )

    def test_rejects_mismatch_and_negatives(self) -> None:
        with self.assertRaises(ValueError):
            split_exact("10.00", [(1, "2.50"), (2, "7.49")])
        with self.assertRaises(ValueError):
            split_exact("10.00", [(1, "-1.00"), (2, "11.00")])


class NetBalancesTests(unittest.TestCase):
    def test_balances_sum_to_zero_and_feed_the_simplifier(self) -> None:
        balances = net_balances(
            [
                (1, "30.00", {1: "10.00", 2: "10.00", 3: "10.00"}),
                (2, "9.00", {1: "3.00", 2: "3.00", 3: "3.00"}),
            ]
        )
        self.assertEqual(balances, {1: Decimal("17.00"), 2: Decimal("-4.00"), 3: Decimal("-13.00")})
        self.assertEqual(sum(balances.values()), Decimal("0.00"))

    def test_rejects_expense_whose_shares_do_not_match_total(self) -> None:
        with self.assertRaises(ValueError):
            net_balances([(1, "10.00", {1: "5.00", 2: "4.99"})])


if __name__ == "__main__":
    unittest.main()
