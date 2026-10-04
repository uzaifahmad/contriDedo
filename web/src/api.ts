import type { ExpenseCreatePayload } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function createTripExpense(
  tripId: number,
  payload: ExpenseCreatePayload,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/trips/${tripId}/expenses`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(`The expense could not be saved (${response.status}).`);
  }
}
