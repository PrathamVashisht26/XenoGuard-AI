"use client";

import { useState, useEffect } from "react";
import { getInsights } from "@/lib/api";
import type { Insight } from "@/types";

const SEVERITY_CONFIG = {
  CRITICAL: { icon: "🔴", cls: "critical", label: "Critical" },
  WARNING:  { icon: "⚠️",  cls: "warning",  label: "Warning" },
  INFO:     { icon: "💡", cls: "info",     label: "Info" },
};

export default function InsightsTab({ sessionId, status }: { sessionId: string; status: string }) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status !== "COMPLETED") return;
    getInsights(sessionId).then((r) => { setInsights(r.data.insights); setLoading(false); }).catch(() => setLoading(false));
  }, [sessionId, status]);

  if (status !== "COMPLETED") return <Waiting />;
  if (loading) return <Loader />;

  return (
    <div className="animate-fade-in-up">
      <div className="section-header">
        <div>
          <div className="section-title">AI Insights</div>
          <div className="section-subtitle">Automatically generated business intelligence from your dataset</div>
        </div>
        <span className="pill pill-info">🤖 {insights.length} insights generated</span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {insights.map((insight, i) => {
          const cfg = SEVERITY_CONFIG[insight.severity] || SEVERITY_CONFIG.INFO;
          return (
            <div key={i} className={`insight-card ${cfg.cls} animate-fade-in-up`} style={{ animationDelay: `${i * 0.05}s` }}>
              <div style={{ fontSize: 28, lineHeight: 1 }}>{cfg.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700 }}>{insight.title}</h3>
                  <span className={`pill pill-${cfg.cls}`}>{cfg.label}</span>
                  {insight.affected_count > 0 && (
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      {insight.affected_count.toLocaleString()} records affected
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.65 }}>{insight.body}</p>
              </div>
            </div>
          );
        })}
      </div>

      {insights.length === 0 && (
        <div style={{ textAlign: "center", padding: 60 }}>
          <p style={{ color: "var(--text-muted)" }}>No insights generated. Dataset may have no significant patterns.</p>
        </div>
      )}
    </div>
  );
}

function Waiting() { return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>⏳ Insights will appear after processing completes.</div>; }
function Loader() { return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>Loading insights…</div>; }
