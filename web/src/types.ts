export type CalculationMethod = "equal" | "percentage" | "exact";

export interface ExpenseSplitPayload {
  user_id: number;
  amount_owed: string;
  calculation_method: CalculationMethod;
}

export interface ExpenseCreatePayload {
  description: string;
  total_amount: string;
  payer_id: number;
  splits: ExpenseSplitPayload[];
}

export interface TripMember {
  id: number;
  name: string;
  initials: string;
  color: string;
}

export interface TripSummary {
  id: number;
  title: string;
  destination: string;
  dateRange: string;
  totalSpent: string;
  memberCount: number;
}

export interface ExpenseItem {
  id: number;
  description: string;
  category: "Food" | "Stay" | "Travel" | "Activity";
  payerId: number;
  amount: string;
  date: string;
}
