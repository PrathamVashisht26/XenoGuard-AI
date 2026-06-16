"use client";

import { useState, useEffect } from "react";
import { getTransactions, getErrors } from "@/lib/api";
import type { Transaction, ValidationError } from "@/types";

export default function ValidationTab({ sessionId, status }: { sessionId: string; status: string }) {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<"all" | "valid" | "invalid">("all");
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status !== "COMPLETED") return;
    setLoading(true);
    getTransactions(sessionId, page, filter)
      .then((r) => { setTxns(r.data.rows); setTotal(r.data.total); setLoading(false); })
      .catch(() => setLoading(false));
  }, [sessionId, status, page, filter]);

  const openDrawer = async (txn: Transaction) => {
    setSelectedTxn(txn);
    const r = await getErrors(sessionId, txn.id);
    setErrors(r.data.errors);
  };

  if (status !== "COMPLETED") {
    return <Waiting />;
  }

  return (
    <div className="animate-fade-in-up">
      <div className="section-header">
        <div>
          <div className="section-title">Validation Explorer</div>
          <div className="section-subtitle">{total.toLocaleString()} rows · click any row to view errors</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {(["all", "valid", "invalid"] as const).map((f) => (
            <button
              key={f}
              onClick={() => { setFilter(f); setPage(1); }}
              className={`nav-tab ${filter === f ? "active" : ""}`}
              style={{ padding: "6px 14px", fontSize: 13 }}
            >
              {f === "all" ? "All" : f === "valid" ? "✅ Valid" : "❌ Invalid"}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card" style={{ overflowX: "auto", marginBottom: 20 }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Row #</th>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Country</th>
              <th>Status</th>
              <th>Errors</th>
              <th>Fixed</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>Loading…</td></tr>
            ) : txns.length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>No rows found</td></tr>
            ) : txns.map((txn) => (
              <tr key={txn.id} onClick={() => openDrawer(txn)}>
                <td style={{ color: "var(--text-muted)" }}>{txn.row_number}</td>
                <td><code style={{ fontSize: 11, color: "var(--accent)" }}>{txn.data?.order_id || "—"}</code></td>
                <td>{txn.data?.customer_name || "—"}</td>
                <td>{txn.data?.country_code || "—"}</td>
                <td>
                  <span className={`pill ${txn.is_valid ? "pill-completed" : "pill-error"}`}>
                    {txn.is_valid ? "✅ Valid" : "❌ Invalid"}
                  </span>
                </td>
                <td>
                  {txn.error_count > 0 ? (
                    <span style={{ fontWeight: 700, color: "#ef4444" }}>{txn.error_count}</span>
                  ) : (
                    <span style={{ color: "var(--text-muted)" }}>—</span>
                  )}
                </td>
                <td>{txn.is_fixed ? <span className="pill pill-warning">🛠️ Fixed</span> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
        <button className="btn-secondary" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>← Prev</button>
        <span style={{ padding: "10px 16px", fontSize: 13, color: "var(--text-secondary)" }}>
          Page {page} · {Math.ceil(total / 50)} pages
        </span>
        <button className="btn-secondary" onClick={() => setPage(p => p + 1)} disabled={page * 50 >= total}>Next →</button>
      </div>

      {selectedTxn && (
        <>
          <div className="drawer-overlay" onClick={() => setSelectedTxn(null)} />
          <div className="drawer">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700 }}>Row {selectedTxn.row_number} — Error Details</h3>
              <button onClick={() => setSelectedTxn(null)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", fontSize: 20 }}>×</button>
            </div>

            {errors.length === 0 ? (
              <p style={{ color: "var(--success)", fontWeight: 600 }}>✅ This row has no errors.</p>
            ) : errors.map((err) => (
              <div key={err.id} style={{
                marginBottom: 16, padding: 16, borderRadius: 10,
                background: err.severity === "ERROR" ? "rgba(239,68,68,0.06)" : "rgba(245,158,11,0.06)",
                border: `1px solid ${err.severity === "ERROR" ? "rgba(239,68,68,0.2)" : "rgba(245,158,11,0.2)"}`,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <code style={{ fontSize: 11, color: err.severity === "ERROR" ? "#ef4444" : "#f59e0b" }}>
                    {err.error_code}
                  </code>
                  <span className={`pill ${err.severity === "ERROR" ? "pill-error" : "pill-warning"}`}>{err.severity}</span>
                </div>
                {err.field_name && (
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
                    Field: <strong style={{ color: "var(--text-secondary)" }}>{err.field_name}</strong>
                    {" · "}Value: <code style={{ color: "#fca5a5" }}>{err.raw_value || "(empty)"}</code>
                  </div>
                )}
                <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-primary)", marginBottom: 10 }}>
                  {err.explanation}
                </p>
                {err.fix_suggestion && (
                  <div style={{ padding: "8px 12px", background: "rgba(16,185,129,0.08)", borderRadius: 8, border: "1px solid rgba(16,185,129,0.2)", fontSize: 12, color: "#6ee7b7" }}>
                    💡 <strong>Fix:</strong> {err.fix_suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
function Waiting() { return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>⏳ Waiting for validation to complete…</div>; }
