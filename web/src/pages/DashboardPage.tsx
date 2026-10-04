import { useState } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Bell,
  CarFront,
  ChevronDown,
  CircleHelp,
  Coffee,
  House,
  Plus,
  Settings2,
  ShoppingBasket,
  Utensils,
  Wallet,
} from "lucide-react";
import Brand from "../components/Brand";
import ExpenseDialog from "../components/ExpenseDialog";
import { currentTrip, initialExpenses, tripMembers } from "../data";
import type { ExpenseCreatePayload, ExpenseItem } from "../types";

const categoryIcons = {
  Food: Utensils,
  Stay: House,
  Travel: CarFront,
  Activity: ShoppingBasket,
};

function money(value: string) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(value));
}

function addMoney(left: string, right: string) {
  const toCents = (amount: string) => {
    const [dollars, cents = ""] = amount.split(".");
    return BigInt(dollars) * 100n + BigInt(cents.padEnd(2, "0"));
  };
  const total = toCents(left) + toCents(right);
  return `${total / 100n}.${(total % 100n).toString().padStart(2, "0")}`;
}

export default function DashboardPage() {
  const [expenses, setExpenses] = useState(initialExpenses);
  const [totalSpent, setTotalSpent] = useState(currentTrip.totalSpent);
  const [showExpenseForm, setShowExpenseForm] = useState(false);
  const [notice, setNotice] = useState("");

  function handleSaved(payload: ExpenseCreatePayload) {
    const newExpense: ExpenseItem = {
      id: Date.now(),
      description: payload.description,
      category: "Food",
      payerId: payload.payer_id,
      amount: payload.total_amount,
      date: "Just now",
    };
    setExpenses((previous) => [newExpense, ...previous]);
    setTotalSpent((previous) => addMoney(previous, payload.total_amount));
    setShowExpenseForm(false);
    setNotice("Expense added to the trip.");
    window.setTimeout(() => setNotice(""), 3200);
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <Brand light />
        <div className="sidebar-section-label">YOUR SPACE</div>
        <button className="side-link active" type="button"><Wallet size={18} /> Overview</button>
        <button className="side-link" type="button"><span className="side-link-icon"><span>✈</span></span> Trips <span className="side-count">3</span></button>
        <button className="side-link" type="button"><ArrowDownLeft size={18} /> Balances</button>

        <div className="sidebar-trip-heading"><span>YOUR TRIPS</span><button aria-label="Add a trip" type="button"><Plus size={16} /></button></div>
        <button className="trip-nav-item selected" type="button"><span className="trip-nav-dot mint" />Hudson Valley<span className="trip-nav-notice" /></button>
        <button className="trip-nav-item" type="button"><span className="trip-nav-dot peach" />Portland, ME</button>
        <button className="trip-nav-item" type="button"><span className="trip-nav-dot blue" />Summer in Spain</button>

        <div className="sidebar-spacer" />
        <button className="side-link" type="button"><Settings2 size={18} /> Settings</button>
        <button className="side-link" type="button"><CircleHelp size={18} /> Help & feedback</button>
        <div className="sidebar-profile">
          <span className="member-avatar profile-avatar">NC</span>
          <span><strong>Nadia Chen</strong><small>Personal account</small></span>
          <ChevronDown size={15} />
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-topbar">
          <div className="breadcrumb"><span>Trips</span><span className="breadcrumb-separator">/</span><strong>Hudson Valley Weekend</strong></div>
          <div className="topbar-actions">
            <button aria-label="Notifications" className="icon-button notification-button" type="button"><Bell size={18} /><i /></button>
            <span className="member-avatar top-avatar">NC</span>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="trip-heading-row">
            <div>
              <div className="trip-meta"><span className="trip-status-dot" />CURRENT TRIP <span className="meta-divider">·</span> {currentTrip.dateRange}</div>
              <h1>{currentTrip.title}</h1>
              <p className="trip-location"><span>⌖</span> {currentTrip.destination} <span className="meta-divider">·</span> <button type="button">{currentTrip.memberCount} people <ChevronDown size={14} /></button></p>
            </div>
            <button className="button button-primary add-expense-button" onClick={() => setShowExpenseForm(true)} type="button"><Plus size={18} /> Add expense</button>
          </section>

          <section aria-label="Trip spending summary" className="stats-row">
            <article className="stat-block stat-total">
              <span className="stat-label">TOTAL SPENT</span>
              <strong>{money(totalSpent)}</strong>
              <span className="stat-note"><span className="trend-up"><ArrowUpRight size={14} /> 12%</span> vs. your last trip</span>
            </article>
            <article className="stat-block">
              <span className="stat-label">YOUR SHARE</span>
              <strong>$569.12</strong>
              <span className="stat-note">20% average share</span>
            </article>
            <article className="stat-block stat-owed">
              <span className="stat-label">OWED TO YOU</span>
              <strong>$342.88</strong>
              <span className="stat-note">From 2 travelers</span>
            </article>
            <div className="stat-people" aria-label="Trip members">
              <div className="avatar-stack">
                {tripMembers.map((member) => <span className="member-avatar" key={member.id} style={{ backgroundColor: member.color }}>{member.initials}</span>)}
              </div>
              <span>Your crew</span>
            </div>
          </section>

          <div className="dashboard-grid">
            <section className="activity-section">
              <div className="section-title-row">
                <div><span className="section-kicker">THE RUNNING TAB</span><h2>Ledger activity</h2></div>
                <button className="quiet-action" type="button">All expenses <ArrowUpRight size={15} /></button>
              </div>
              <div className="expense-list">
                {expenses.map((expense) => {
                  const Icon = categoryIcons[expense.category];
                  const payer = tripMembers.find((member) => member.id === expense.payerId);
                  return (
                    <article className="expense-row" key={expense.id}>
                      <span className={`expense-icon icon-${expense.category.toLowerCase()}`}><Icon size={18} strokeWidth={1.8} /></span>
                      <span className="expense-description"><strong>{expense.description}</strong><small>{payer?.name.split(" ")[0] ?? "You"} paid <span>·</span> {expense.date}</small></span>
                      <span className="expense-category">{expense.category}</span>
                      <strong className="expense-amount">{money(expense.amount)}</strong>
                    </article>
                  );
                })}
              </div>
              <button className="load-more" type="button">See all 8 expenses <ArrowUpRight size={15} /></button>
            </section>

            <aside className="right-rail">
              <section className="balances-section">
                <div className="section-title-row compact-title">
                  <div><span className="section-kicker">NICE & CLEAR</span><h2>Balances</h2></div>
                  <button aria-label="More balance options" className="more-button" type="button">···</button>
                </div>
                <div className="balance-highlight">
                  <span className="balance-icon"><ArrowDownLeft size={17} /></span>
                  <div><small>Coming your way</small><strong>$342.88</strong></div>
                  <span className="balance-count">2</span>
                </div>
                <div className="balance-person">
                  <span className="member-avatar" style={{ backgroundColor: tripMembers[1].color }}>MS</span>
                  <span><strong>Marco Silva</strong><small>settle up anytime</small></span>
                  <b>+$164.20</b>
                </div>
                <div className="balance-person">
                  <span className="member-avatar" style={{ backgroundColor: tripMembers[2].color }}>ER</span>
                  <span><strong>Elena Rostova</strong><small>settle up anytime</small></span>
                  <b>+$178.68</b>
                </div>
                <div className="balance-you-owe"><ArrowUpRight size={15} /><span>3 direct transfers</span><strong>optimized</strong></div>
                <button className="settle-button" type="button">Simplify & settle <ArrowUpRight size={15} /></button>
              </section>

              <section className="trip-note">
                <div className="trip-note-top"><span className="note-sun">✳</span><span>GOOD TO KNOW</span></div>
                <p>You're all caught up on adding expenses. Keep the little ones coming.</p>
                <div className="note-footer"><Coffee size={15} /> Even the coffee counts.</div>
              </section>
            </aside>
          </div>
        </div>
      </main>

      {notice && <div className="toast-message" role="status">{notice}</div>}
      {showExpenseForm && (
        <ExpenseDialog
          members={tripMembers}
          onClose={() => setShowExpenseForm(false)}
          onSaved={handleSaved}
          tripId={currentTrip.id}
        />
      )}
    </div>
  );
}
