import type { ExpenseItem, TripMember, TripSummary } from "./types";

export const currentTrip: TripSummary = {
  id: 42,
  title: "Hudson Valley Weekend",
  destination: "Gardiner & Beacon, NY",
  dateRange: "OCT 12 — OCT 15",
  totalSpent: "2845.60",
  memberCount: 5,
};

export const tripMembers: TripMember[] = [
  { id: 101, name: "Nadia Chen", initials: "NC", color: "#d9e9dc" },
  { id: 102, name: "Marco Silva", initials: "MS", color: "#f4d9c7" },
  { id: 103, name: "Elena Rostova", initials: "ER", color: "#d9e2f2" },
  { id: 104, name: "Devon Vance", initials: "DV", color: "#f2e6b9" },
  { id: 105, name: "Maya Patel", initials: "MP", color: "#e6dcef" },
];

export const initialExpenses: ExpenseItem[] = [
  {
    id: 1,
    description: "Wildflower Farms cabin stay",
    category: "Stay",
    payerId: 101,
    amount: "950.00",
    date: "Oct 15",
  },
  {
    id: 2,
    description: "Beacon Cider House tasting & lunch",
    category: "Food",
    payerId: 102,
    amount: "182.00",
    date: "Oct 14",
  },
  {
    id: 3,
    description: "Storm King Art Center passes",
    category: "Activity",
    payerId: 103,
    amount: "125.00",
    date: "Oct 14",
  },
  {
    id: 4,
    description: "Firewood & campfire coffee",
    category: "Food",
    payerId: 104,
    amount: "58.00",
    date: "Oct 13",
  },
];
