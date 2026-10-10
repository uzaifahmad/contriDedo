import { useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowLeft, Check, LoaderCircle, X } from "lucide-react";
import { createTripExpense, newIdempotencyKey } from "../api";
import { buildExpenseSplits, normalizeMoney } from "../money";
import type { CalculationMethod, ExpenseCreatePayload, TripMember } from "../types";

interface ExpenseDialogProps {
  tripId: number;
  members: TripMember[];
  onClose: () => void;
  onSaved: (payload: ExpenseCreatePayload) => void;
}

export default function ExpenseDialog({
  tripId,
  members,
  onClose,
  onSaved,
}: ExpenseDialogProps) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [payerId, setPayerId] = useState(members[0]?.id ?? 0);
  const [participantIds, setParticipantIds] = useState(members.map((member) => member.id));
  const [splitMethod, setSplitMethod] = useState<CalculationMethod>("equal");
  const [splitValues, setSplitValues] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  // One key per distinct payload: a retry after a failure reuses it, an edited expense gets a new one.
  const attempt = useRef<{ body: string; key: string } | null>(null);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !saving) onClose();
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [onClose, saving]);

  let preview: ReturnType<typeof buildExpenseSplits> = [];
  let previewError = "";
  try {
    if (amount && participantIds.length > 0) {
      preview = buildExpenseSplits(amount, participantIds, splitMethod, splitValues);
    }
  } catch (caught) {
    preview = [];
    previewError = caught instanceof Error ? caught.message : "Check the split values.";
  }

  function toggleParticipant(userId: number) {
    setParticipantIds((current) =>
      current.includes(userId)
        ? current.filter((id) => id !== userId)
        : [...current, userId],
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      const payload: ExpenseCreatePayload = {
        description: description.trim(),
        total_amount: normalizeMoney(amount),
        payer_id: payerId,
        splits: buildExpenseSplits(amount, participantIds, splitMethod, splitValues),
      };
      const body = JSON.stringify(payload);
      if (attempt.current?.body !== body) {
        attempt.current = { body, key: newIdempotencyKey() };
      }
      await createTripExpense(tripId, payload, { idempotencyKey: attempt.current.key });
      onSaved(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save this expense.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="dialog-scrim" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section aria-labelledby="expense-title" aria-modal="true" className="expense-dialog" role="dialog">
        <div className="dialog-topline">
          <button aria-label="Close add expense" className="icon-button" onClick={onClose} type="button">
            <X size={19} />
          </button>
          <span className="dialog-step">NEW EXPENSE · 1 OF 1</span>
          <span className="dialog-top-spacer" />
        </div>
        <div className="dialog-heading">
          <span className="dialog-kicker">Hudson Valley weekend</span>
          <h2 id="expense-title">Add to the trip tab</h2>
          <p>Everyone will see the expense and their share.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="expense-description">What was it for?</label>
          <input
            autoFocus
            className="form-input"
            id="expense-description"
            maxLength={120}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="e.g. Dinner at Silvia"
            required
            value={description}
          />

          <div className="form-two-col">
            <div>
              <label className="field-label" htmlFor="expense-amount">Total amount</label>
              <div className="amount-input-wrap">
                <span>$</span>
                <input
                  className="form-input amount-input"
                  id="expense-amount"
                  inputMode="decimal"
                  onChange={(event) => setAmount(event.target.value)}
                  placeholder="0.00"
                  required
                  value={amount}
                />
              </div>
            </div>
            <div>
              <label className="field-label" htmlFor="expense-payer">Paid by</label>
              <select
                className="form-input select-input"
                id="expense-payer"
                onChange={(event) => setPayerId(Number(event.target.value))}
                value={payerId}
              >
                {members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}
              </select>
            </div>
          </div>

          <div className="split-method-section">
            <span className="field-label">Split method</span>
            <div aria-label="Split method" className="split-method-control" role="group">
              {(["equal", "percentage", "exact"] as const).map((method) => (
                <button
                  aria-pressed={splitMethod === method}
                  className={splitMethod === method ? "split-method-choice is-active" : "split-method-choice"}
                  key={method}
                  onClick={() => setSplitMethod(method)}
                  type="button"
                >
                  {method[0].toUpperCase() + method.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="participant-heading">
            <div><span className="field-label">Split between</span><span className="field-hint">Choose who shares this expense</span></div>
            <span className="participant-count">{participantIds.length} of {members.length}</span>
          </div>
          <div className="participant-list">
            {members.map((member) => {
              const selected = participantIds.includes(member.id);
              return (
                <label className={`participant-row ${selected ? "is-selected" : ""}`} key={member.id}>
                  <span className="member-avatar" style={{ backgroundColor: member.color }}>{member.initials}</span>
                  <span className="participant-name">{member.name}</span>
                  <span className={`checkbox-mark ${selected ? "checked" : ""}`} aria-hidden="true">{selected && <Check size={13} />}</span>
                  <input checked={selected} onChange={() => toggleParticipant(member.id)} type="checkbox" />
                </label>
              );
            })}
          </div>

          {splitMethod !== "equal" && participantIds.length > 0 && (
            <div className="split-value-list">
              {participantIds.map((userId) => {
                const member = members.find((person) => person.id === userId);
                const inputId = `split-value-${userId}`;
                return (
                  <div className="split-value-row" key={userId}>
                    <label htmlFor={inputId}>{member?.name ?? `Traveler ${userId}`}</label>
                    <div className="split-value-input-wrap">
                      <input
                        aria-label={`${splitMethod} share for ${member?.name ?? userId}`}
                        id={inputId}
                        inputMode="decimal"
                        onChange={(event) => setSplitValues((current) => ({ ...current, [userId]: event.target.value }))}
                        placeholder={splitMethod === "exact" ? "0.00" : "0.00"}
                        value={splitValues[userId] ?? ""}
                      />
                      <span>{splitMethod === "exact" ? "$" : "%"}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {preview.length > 0 && (
            <div className="split-preview">
              <span className="preview-heading">{splitMethod === "percentage" ? "Calculated shares" : "Each person pays"}</span>
              {preview.map((split) => {
                const person = members.find((member) => member.id === split.user_id);
                return <span key={split.user_id}>{person?.name.split(" ")[0]} <strong>${split.amount_owed}</strong></span>;
              })}
              {splitMethod === "equal" && <span className="split-rounding-note">Remainder cents go to the first people listed.</span>}
            </div>
          )}

          {previewError && amount && <p className="form-error" role="status">{previewError}</p>}

          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="dialog-actions">
            <button className="text-link back-link" onClick={onClose} type="button"><ArrowLeft size={16} /> Cancel</button>
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />}
              {saving ? "Saving…" : "Add expense"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
