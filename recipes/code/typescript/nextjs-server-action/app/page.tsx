"use client";

import { useActionState } from "react";

import { MAX_DESCRIPTION_LENGTH, MAX_RECORDS } from "../lib/limits";
import { generateRecords, type RecordsState } from "./actions";

// The method's own sample, as its inputs give it at the cookbook's release: test tickets for a customer service team's triage.
const SAMPLE: RecordsState = {
  status: "idle",
  values: {
    description: [
      "Test tickets for our customer service triage. Written for a Pipelex example: the shop is not a real one, and every customer must be invented.",
      "We are the customer service team of an online shop selling small kitchen appliances (kettles, toasters, coffee machines, blenders and hand mixers) in France, Belgium and Switzerland. Customers write to us by email or through the contact form on the site, in French or in English.",
      "Each ticket gives the channel (email or contact form), the customer's name, the language, the order number when the customer gives one (the letter C and eight digits), the subject line, the message as the customer wrote it, and the queue and the priority our triage should give it.",
      "The queues are Orders and delivery, Returns and refunds, Product help, Warranty and repairs, Billing, and Other. A ticket is urgent when the customer reports a safety problem (smoke, a burning smell, an electric shock) or a payment taken twice, high when a delivery is more than five days late or a refund is overdue, and normal otherwise.",
      "Make them read like the messages we actually get: some two lines long and annoyed, some long and polite, a few with typos or written on a phone, one that asks two things at once, one that gives no order number. Cover every queue at least once.",
    ].join("\n\n"),
    count: "10",
  },
};

export default function Page() {
  const [state, submit, pending] = useActionState(generateRecords, SAMPLE);
  const { values } = state;
  // Every record carries the fields the description names, in its order, so the first record's names head the table.
  const columns = state.status === "generated" ? (state.records[0]?.fields.map((field) => field.name) ?? []) : [];
  return (
    <main>
      <h1>Generate test records</h1>
      {/* React resets the form once its action has run, each field to its default: the values the action sent back. */}
      <form action={submit} style={{ display: "grid", gap: "0.75rem" }}>
        <label style={{ display: "grid", gap: "0.25rem" }}>
          What the records are for, the fields each carries, the rules deciding a value, and the cases to cover
          <textarea name="description" required rows={14} maxLength={MAX_DESCRIPTION_LENGTH} defaultValue={values.description} />
        </label>
        <label>
          Records <input name="count" type="number" required min={1} max={MAX_RECORDS} step={1} defaultValue={values.count} />
        </label>
        <button type="submit" disabled={pending}>
          {pending ? "Generating…" : "Generate them"}
        </button>
      </form>
      {state.status === "refused" && <p role="alert">{state.message}</p>}
      {state.status === "generated" && (
        <section>
          <table style={{ borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr>
                <th>case</th>
                {columns.map((name) => (
                  <th key={name}>{name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {state.records.map((record, index) => (
                <tr key={index} style={{ verticalAlign: "top", borderTop: "1px solid #ddd" }}>
                  <td>{record.case}</td>
                  {columns.map((name) => (
                    <td key={name} style={{ whiteSpace: "pre-wrap" }}>
                      {record.fields.find((field) => field.name === name)?.value ?? ""}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <small>run {state.runId}</small>
        </section>
      )}
    </main>
  );
}
