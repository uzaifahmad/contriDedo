import type { ExpenseSplitPayload } from "./types";

function amountToCents(amount: string, allowZero = false): bigint {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(amount.trim());
  if (!match) {
    throw new Error("Enter an amount with up to two decimal places.");
  }

  const dollars = BigInt(match[1]);
  const cents = BigInt((match[2] ?? "").padEnd(2, "0") || "0");
  const total = dollars * 100n + cents;
  if (total < 0n || (!allowZero && total === 0n)) {
    throw new Error("Amount must be greater than zero.");
  }
  return total;
}

function centsToAmount(cents: bigint): string {
  return `${cents / 100n}.${(cents % 100n).toString().padStart(2, "0")}`;
}

export function normalizeMoney(amount: string): string {
  return centsToAmount(amountToCents(amount));
}

export function allocateEqualShares(
  totalAmount: string,
  participantIds: number[],
): ExpenseSplitPayload[] {
  if (participantIds.length === 0) {
    throw new Error("Choose at least one person to split with.");
  }
  if (new Set(participantIds).size !== participantIds.length) {
    throw new Error("Each person can only be included once.");
  }

  const totalCents = amountToCents(totalAmount);
  const baseShare = totalCents / BigInt(participantIds.length);
  const remainder = Number(totalCents % BigInt(participantIds.length));

  return participantIds.map((userId, index) => ({
    user_id: userId,
    amount_owed: centsToAmount(baseShare + (index < remainder ? 1n : 0n)),
    calculation_method: "equal",
  }));
}

function percentageToBasisPoints(value: string): bigint {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(value.trim());
  if (!match) {
    throw new Error("Enter a valid percentage.");
  }

  const basisPoints = BigInt(match[1]) * 100n + BigInt((match[2] ?? "").padEnd(2, "0") || "0");
  if (basisPoints > 10_000n) {
    throw new Error("Percentages must be between 0 and 100.");
  }
  return basisPoints;
}

export function buildExpenseSplits(
  totalAmount: string,
  participantIds: number[],
  method: "equal" | "percentage" | "exact",
  values: Record<number, string> = {},
): ExpenseSplitPayload[] {
  if (method === "equal") {
    return allocateEqualShares(totalAmount, participantIds);
  }
  if (participantIds.length === 0 || new Set(participantIds).size !== participantIds.length) {
    throw new Error("Choose unique participants for this expense.");
  }

  const totalCents = amountToCents(totalAmount);
  if (method === "exact") {
    const shares = participantIds.map((userId) => ({
      userId,
      cents: amountToCents(values[userId] ?? "", true),
    }));
    if (shares.reduce((sum, share) => sum + share.cents, 0n) !== totalCents) {
      throw new Error("Exact shares must add up to the total.");
    }
    return shares.map(({ userId, cents }) => ({
      user_id: userId,
      amount_owed: centsToAmount(cents),
      calculation_method: method,
    }));
  }

  const percentages = participantIds.map((userId, index) => ({
    userId,
    index,
    basisPoints: percentageToBasisPoints(values[userId] ?? ""),
  }));
  if (percentages.reduce((sum, share) => sum + share.basisPoints, 0n) !== 10_000n) {
    throw new Error("Percentages must add up to 100%.");
  }

  const shares = percentages.map((share) => {
    const product = totalCents * share.basisPoints;
    return { ...share, cents: product / 10_000n, remainder: product % 10_000n };
  });
  let remainder = totalCents - shares.reduce((sum, share) => sum + share.cents, 0n);
  const remainderRecipients = [...shares]
    .sort((left, right) => left.remainder === right.remainder
      ? left.index - right.index
      : left.remainder > right.remainder ? -1 : 1)
    .slice(0, Number(remainder));
  const remainderIds = new Set(remainderRecipients.map((share) => share.userId));
  return shares.map((share) => {
    const cents = share.cents + (remainderIds.has(share.userId) ? 1n : 0n);
    remainder -= remainderIds.has(share.userId) ? 1n : 0n;
    return {
      user_id: share.userId,
      amount_owed: centsToAmount(cents),
      calculation_method: method,
    };
  });
}
