"use client";

import { useState, useEffect } from "react";
import { getAudit } from "@/lib/api";
import type { AuditEvent } from "@/types";

const EVENT_ICONS: Record<string, string> = {
  FILE_UPLOADED:       "📤",
  VALIDATION_STARTED:  "▶️",
  VALIDATION_COMPLETED:"✅",
  FIX_ACCEPTED:        "🛠️",
  BULK_FIX_ACCEPTED:   "⚡",
  DOWNLOAD:            "⬇️",
};

export default function AuditTab({ sessionId, status }: { sessionId: string; status: string }) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAudit(sessionId).then((r) => { setEvents(r.data.events); setLoading(false); }).catch(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>Loading audit trail…</div>;

  return (
    <div className="animate-fade-in-up">
      <div className="section-header">
        <div>
          <div className="section-title">Audit Trail</div>
          <div className="section-subtitle">Immutable event log — all actions timestamped</div>
        </div>
        <span className="pill pill-info">{events.length} events</span>
      </div>

      {events.length === 0 ? (
        <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>No events recorded yet.</p>
      ) : (
        <div style={{ position: "relative" }}>
          {/* Timeline line */}
          <div style={{
            position: "absolute", left: 22, top: 0, bottom: 0,
            width: 2, background: "var(--border)",
          }} />

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {events.map((ev, i) => (
              <div key={i} style={{ display: "flex", gap: 16, paddingLeft: 8, animationDelay: `${i * 0.03}s` }} className="animate-fade-in-up">
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  background: "var(--bg-card)",
                  border: "2px solid var(--border-bright)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, flexShrink: 0, zIndex: 1,
                }}>
                  {EVENT_ICONS[ev.event_type] || "•"}
                </div>
                <div className="glass-card" style={{ flex: 1, padding: "12px 16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{ev.event_type.replace(/_/g, " ")}</span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {new Date(ev.occurred_at).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                    Actor: <strong>{ev.actor}</strong>
                  </div>
                  {ev.event_data && Object.keys(ev.event_data).length > 0 && (
                    <pre style={{
                      marginTop: 8, fontSize: 11, color: "var(--text-muted)",
                      background: "var(--bg-secondary)", padding: "6px 10px",
                      borderRadius: 6, overflow: "auto", maxHeight: 80,
                    }}>
                      {JSON.stringify(ev.event_data, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
