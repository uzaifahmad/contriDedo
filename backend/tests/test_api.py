import unittest

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from contri_dedo.api import create_app
from contri_dedo.database import normalize_database_url
from contri_dedo.models import ExpenseSplit


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app("sqlite://", create_tables=True)
        self.client = TestClient(self.app)
        self.owner_id, token = self._sign_up("nadia@example.com", "Nadia")
        self.headers = {"Authorization": f"Bearer {token}"}
        trip_response = self.client.post(
            "/api/trips", json={"name": "Weekend", "destination": "Beacon"}, headers=self.headers
        )
        self.assertEqual(trip_response.status_code, 201, trip_response.text)
        self.trip_id = trip_response.json()["id"]
        self.member_ids = [self.owner_id]
        for email, name in [("marco@example.com", "Marco"), ("elena@example.com", "Elena")]:
            member_id, _ = self._sign_up(email, name)
            self.member_ids.append(member_id)
            response = self.client.post(
                f"/api/trips/{self.trip_id}/members", json={"email": email}, headers=self.headers
            )
            self.assertEqual(response.status_code, 201, response.text)

    def _sign_up(self, email: str, name: str) -> tuple[int, str]:
        response = self.client.post(
            "/api/auth/sign-up",
            json={"email": email, "password": "correct-horse-42", "display_name": name},
        )
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        return body["user"]["id"], body["access_token"]

    def _expense(self, description: str = "Market groceries") -> dict[str, object]:
        return {
            "description": description,
            "total_amount": "24.00",
            "payer_id": self.owner_id,
            "currency": "USD",
            "category": "Food",
            "splits": [
                {"user_id": member_id, "amount_owed": "8.00", "calculation_method": "exact"}
                for member_id in self.member_ids
            ],
        }

    def test_authentication_and_trip_membership(self) -> None:
        self.assertEqual(self.client.get("/api/trips").status_code, 401)
        sign_in = self.client.post(
            "/api/auth/sign-in", json={"email": "NADIA@example.com", "password": "correct-horse-42"}
        )
        self.assertEqual(sign_in.status_code, 200, sign_in.text)
        trips = self.client.get("/api/trips", headers=self.headers)
        self.assertEqual([trip["name"] for trip in trips.json()], ["Weekend"])
        detail = self.client.get(f"/api/trips/{self.trip_id}", headers=self.headers).json()
        self.assertEqual([person["id"] for person in detail["members"]], self.member_ids)

    def test_local_frontend_cors_preflight_allows_bearer_requests(self) -> None:
        response = self.client.options(
            "/api/trips",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")


    def test_create_list_expense_and_compute_simplified_balances(self) -> None:
        created = self.client.post(
            f"/api/trips/{self.trip_id}/expenses", json=self._expense(), headers=self.headers
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["total_amount"], "24.00")
        self.assertEqual(created.json()["currency"], "USD")
        listed = self.client.get(f"/api/trips/{self.trip_id}/expenses", headers=self.headers)
        self.assertEqual(len(listed.json()), 1)

        balances = self.client.get(f"/api/trips/{self.trip_id}/balances", headers=self.headers).json()
        by_user = {item["user_id"]: item["balance"] for item in balances["balances"]}
        self.assertEqual(by_user, {self.owner_id: "16.00", self.member_ids[1]: "-8.00", self.member_ids[2]: "-8.00"})
        self.assertEqual(len(balances["simplified_debts"]), 2)

    def test_currency_totals_and_balances_are_not_combined(self) -> None:
        for currency in ("USD", "EUR"):
            payload = self._expense()
            payload["currency"] = currency
            response = self.client.post(
                f"/api/trips/{self.trip_id}/expenses", json=payload, headers=self.headers
            )
            self.assertEqual(response.status_code, 201, response.text)

        detail = self.client.get(f"/api/trips/{self.trip_id}", headers=self.headers).json()
        self.assertEqual(detail["total_spent_by_currency"], {"EUR": "24.00", "USD": "24.00"})
        balances = self.client.get(f"/api/trips/{self.trip_id}/balances", headers=self.headers).json()
        self.assertEqual({row["currency"] for row in balances["balances"]}, {"USD", "EUR"})
        self.assertEqual(len(balances["balances"]), 6)
        self.assertEqual(len(balances["simplified_debts"]), 4)

    def test_equal_split_must_match_server_remainder_rule(self) -> None:
        payload = {
            "description": "Coffee",
            "total_amount": "10.00",
            "payer_id": self.owner_id,
            "splits": [
                {"user_id": self.member_ids[0], "amount_owed": "3.33", "calculation_method": "equal"},
                {"user_id": self.member_ids[1], "amount_owed": "3.33", "calculation_method": "equal"},
                {"user_id": self.member_ids[2], "amount_owed": "3.34", "calculation_method": "equal"},
            ],
        }
        response = self.client.post(f"/api/trips/{self.trip_id}/expenses", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertIn("canonical cent allocation", response.json()["detail"])

    def test_partial_percentage_input_is_rejected(self) -> None:
        payload = self._expense()
        payload["splits"][0]["calculation_method"] = "percentage"  # type: ignore[index]
        payload["splits"][0]["percentage"] = "33.34"  # type: ignore[index]
        for split in payload["splits"][1:]:  # type: ignore[index]
            split["calculation_method"] = "percentage"
        response = self.client.post(f"/api/trips/{self.trip_id}/expenses", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertIn("every split participant", response.json()["detail"])

    def test_expense_rejects_nonmembers_and_mismatched_shares(self) -> None:
        payload = self._expense()
        payload["splits"][-1]["user_id"] = 9999  # type: ignore[index]
        response = self.client.post(f"/api/trips/{self.trip_id}/expenses", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)

        payload = self._expense()
        payload["splits"][0]["amount_owed"] = "7.99"  # type: ignore[index]
        response = self.client.post(f"/api/trips/{self.trip_id}/expenses", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertIn("add up to the total", response.json()["detail"])

    def test_database_rejects_split_for_nonmember(self) -> None:
        response = self.client.post(
            f"/api/trips/{self.trip_id}/expenses", json=self._expense(), headers=self.headers
        )
        self.assertEqual(response.status_code, 201, response.text)
        db = self.app.state.session_factory()
        try:
            db.add(
                ExpenseSplit(
                    trip_id=self.trip_id,
                    expense_id=response.json()["id"],
                    user_id=9999,
                    amount_owed="0.00",
                    calculation_method="exact",
                )
            )
            with self.assertRaises(IntegrityError):
                db.commit()
        finally:
            db.rollback()
            db.close()

    def test_idempotency_replays_original_and_rejects_changed_body(self) -> None:
        headers = {**self.headers, "X-Idempotency-Key": "action-abc"}
        first = self.client.post(f"/api/trips/{self.trip_id}/expenses", json=self._expense(), headers=headers)
        replay = self.client.post(f"/api/trips/{self.trip_id}/expenses", json=self._expense(), headers=headers)
        changed = self.client.post(
            f"/api/trips/{self.trip_id}/expenses", json=self._expense("Different"), headers=headers
        )
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(replay.status_code, 201, replay.text)
        self.assertEqual(replay.json()["id"], first.json()["id"])
        self.assertEqual(changed.status_code, 422)
        self.assertEqual(len(self.client.get(f"/api/trips/{self.trip_id}/expenses", headers=self.headers).json()), 1)


class DatabaseUrlTests(unittest.TestCase):
    def test_postgres_urls_use_psycopg_three(self) -> None:
        self.assertEqual(
            normalize_database_url("postgresql://role:secret@host/db?sslmode=require"),
            "postgresql+psycopg://role:secret@host/db?sslmode=require",
        )
        self.assertEqual(
            normalize_database_url("postgres://role:secret@host/db"),
            "postgresql+psycopg://role:secret@host/db",
        )
        self.assertEqual(normalize_database_url("sqlite:///local.db"), "sqlite:///local.db")


if __name__ == "__main__":
    unittest.main()