"use client";

import { useState, useEffect } from "react";
import { getErrors, acceptFix, acceptAllFixes } from "@/lib/api";
import type { ValidationError } from "@/types";

export default function FixStudioTab({ sessionId, status }: { sessionId: string; status: string }) {
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState<number | null>(null);
  const [acceptingAll, setAcceptingAll] = useState(false);

  const fetchErrors = () => {
    getErrors(sessionId)
      .then((r) => {
        const fixable = r.data.errors.filter((e: ValidationError) => e.fix_action && !e.fix_accepted);
        setErrors(fixable);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    if (status !== "COMPLETED") return;
    fetchErrors();
  }, [sessionId, status]);

  const handleAccept = async (errId: number) => {
    setAccepting(errId);
    await acceptFix(errId);
    setErrors((prev) => prev.filter((e) => e.id !== errId));
    setAccepting(null);
  };

  const handleAcceptAll = async () => {
    setAcceptingAll(true);
    await acceptAllFixes(sessionId);
    setErrors([]);
    setAcceptingAll(false);
  };

  const getFixPreview = (err: ValidationError): string => {
    if (!err.fix_action) return "";
    if (err.fix_action === "STRIP_NON_DIGITS") {
      return (err.raw_value || "").replace(/\D/g, "");
    }
    if (err.fix_action === "NORMALIZE_DATE_ISO") return "YYYY-MM-DD (normalized)";
    if (err.fix_action === "STRIP_CURRENCY_SYMBOLS") {
      return (err.raw_value || "").replace(/[^\d.]/g, "");
    }
    if (err.fix_action === "REMOVE_DUPLICATE_ROW") return "(row will be removed)";
    return "(auto-fixed)";
  };

  if (status !== "COMPLETED") {
    return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>⏳ Waiting for processing…</div>;
  }
  if (loading) return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>Loading Fix Studio…</div>;

  return (
    <div className="animate-fade-in-up">
      <div className="section-header">
        <div>
          <div className="section-title">Fix Studio</div>
          <div className="section-subtitle">Review and apply auto-generated fixes</div>
        </div>
        {errors.length > 0 && (
          <button className="btn-primary" onClick={handleAcceptAll} disabled={acceptingAll} id="accept-all-btn">
            {acceptingAll ? "Applying…" : `⚡ Accept All ${errors.length} Fixes`}
          </button>
        )}
      </div>

      {errors.length === 0 ? (
        <div style={{ textAlign: "center", padding: 80 }}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>🎉</div>
          <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>No Pending Fixes</h3>
          <p style={{ color: "var(--text-secondary)" }}>
            All auto-fixable errors have been accepted, or no automatically fixable issues were detected.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {errors.map((err) => (
            <div key={err.id} className="glass-card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
                <div>
                  <code style={{ fontSize: 12, color: "var(--accent)", marginRight: 10 }}>{err.error_code}</code>
                  <span className={`pill ${err.severity === "ERROR" ? "pill-error" : "pill-warning"}`}>{err.severity}</span>
                  {err.field_name && (
                    <span style={{ marginLeft: 10, fontSize: 12, color: "var(--text-muted)" }}>
                      Field: <strong>{err.field_name}</strong>
                    </span>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    className="btn-success"
                    onClick={() => handleAccept(err.id)}
                    disabled={accepting === err.id}
                    id={`accept-fix-${err.id}`}
                  >
                    {accepting === err.id ? "Applying…" : "✅ Accept"}
                  </button>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 12, alignItems: "center", marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: 11, color: "#ef4444", fontWeight: 600, marginBottom: 4, letterSpacing: "0.06em" }}>BEFORE</div>
                  <div className="diff-before">{err.raw_value || "(empty)"}</div>
                </div>
                <div style={{ fontSize: 20 }}>→</div>
                <div>
                  <div style={{ fontSize: 11, color: "#10b981", fontWeight: 600, marginBottom: 4, letterSpacing: "0.06em" }}>AFTER</div>
                  <div className="diff-after">{getFixPreview(err)}</div>
                </div>
              </div>

              <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                💡 {err.fix_suggestion}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
