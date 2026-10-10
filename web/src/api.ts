import type { ExpenseCreatePayload } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const DEFAULT_TIMEOUT_MS = 15_000;

export interface CreateExpenseOptions {
  /** Reuse the same key when retrying the same request so the server can de-duplicate it. */
  idempotencyKey?: string;
  timeoutMs?: number;
}

/** Works on insecure (plain-http LAN) dev origins where crypto.randomUUID is unavailable. */
export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function readErrorDetail(response: Response): Promise<string | undefined> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object") {
      const { detail, title, message } = body as Record<string, unknown>;
      const text = [detail, title, message].find(
        (value): value is string => typeof value === "string" && value.length > 0,
      );
      return text;
    }
  } catch {
    // Non-JSON error body; fall back to the status code.
  }
  return undefined;
}

export async function createTripExpense(
  tripId: number,
  payload: ExpenseCreatePayload,
  options: CreateExpenseOptions = {},
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.idempotencyKey) {
    headers["X-Idempotency-Key"] = options.idempotencyKey;
  }

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), options.timeoutMs ?? DEFAULT_TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/trips/${tripId}/expenses`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } catch (caught) {
    if (caught instanceof DOMException && caught.name === "AbortError") {
      throw new Error("The server took too long to respond. Check your connection and try again.");
    }
    throw new Error("Could not reach the contriDedo server. Check your connection and try again.");
  } finally {
    window.clearTimeout(timer);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `The expense could not be saved (${response.status}).`);
  }
}
