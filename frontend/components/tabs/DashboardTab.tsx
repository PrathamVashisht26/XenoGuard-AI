"use client";

import { useState, useEffect } from "react";
import { getSummary } from "@/lib/api";
import type { ValidationSummary } from "@/types";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

const CATEGORY_COLORS: Record<string, string> = {
  PHONE: "#6366f1",
  DATE: "#a78bfa",
  EMAIL: "#06b6d4",
  PAYMENT: "#f59e0b",
  CURRENCY: "#10b981",
  PRODUCT: "#3b82f6",
  DUPLICATE: "#ef4444",
  MISSING: "#ec4899",
  INTEGRITY: "#f97316",
};

export default function DashboardTab({ sessionId, status }: { sessionId: string; status: string }) {
  const [summary, setSummary] = useState<ValidationSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status !== "COMPLETED") { setLoading(false); return; }
    getSummary(sessionId).then((r) => { setSummary(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, [sessionId, status]);

  if (status !== "COMPLETED") {
    return (
      <div style={{ textAlign: "center", padding: "80px 0" }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>⏳</div>
        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Processing Your Dataset</h2>
        <p style={{ color: "var(--text-secondary)" }}>
          The validation pipeline is running. The dashboard will load once all chunks are complete.
        </p>
      </div>
    );
  }
  if (loading) return <Loader />;
  if (!summary) return <ErrorMsg msg="Could not load dashboard summary." />;

  const score = summary.health_score;
  const scoreColor = score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";

  const pieData = Object.entries(summary.error_breakdown).map(([k, v]) => ({
    name: k, value: v, color: CATEGORY_COLORS[k] || "#6366f1",
  }));

  const barData = Object.entries(summary.country_breakdown)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([country, count]) => ({ country, count }));

  const topFailures = summary.top_failures.slice(0, 5);

  return (
    <div className="animate-fade-in-up">
      <div style={{ display: "flex", gap: 20, marginBottom: 24, flexWrap: "wrap" }}>
        <div className="glass-card animate-pulse-glow" style={{ padding: "28px 32px", flex: "0 0 auto", minWidth: 220 }}>
          <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.08em", marginBottom: 8 }}>
            HEALTH SCORE
          </div>
          <div style={{ fontSize: 68, fontWeight: 900, lineHeight: 1, color: scoreColor }}>
            {score.toFixed(1)}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>out of 100</div>
          <div style={{ marginTop: 14 }}>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{
                width: `${score}%`,
                background: `linear-gradient(90deg, ${scoreColor}, ${scoreColor}aa)`,
              }} />
            </div>
          </div>
          <div style={{ marginTop: 10, fontSize: 13, fontWeight: 600, color: scoreColor }}>
            {score >= 80 ? "✅ Acceptable Quality" : score >= 50 ? "⚠️ Needs Review" : "🔴 Critical Issues"}
          </div>
        </div>

        <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16, minWidth: 360 }}>
          {[
            { label: "Total Records", value: summary.total_rows.toLocaleString(), icon: "📋", color: "#6366f1" },
            { label: "Valid Records", value: summary.valid_rows.toLocaleString(), icon: "✅", color: "#10b981" },
            { label: "Invalid Records", value: summary.invalid_rows.toLocaleString(), icon: "❌", color: "#ef4444" },
            { label: "Auto-Fixed", value: summary.fixed_rows.toLocaleString(), icon: "🛠️", color: "#f59e0b" },
          ].map((kpi) => (
            <div key={kpi.label} className="kpi-card">
              <div className="kpi-value" style={{ color: kpi.color }}>{kpi.value}</div>
              <div className="kpi-label">{kpi.label}</div>
              <div className="kpi-icon">{kpi.icon}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="glass-card" style={{ padding: 24 }}>
          <div className="section-header">
            <div>
              <div className="section-title">Error Distribution</div>
              <div className="section-subtitle">By validation category</div>
            </div>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={95}
                  dataKey="value" nameKey="name" paddingAngle={3}>
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                  formatter={(val: number) => [val.toLocaleString(), "Errors"]}
                />
                <Legend
                  iconType="circle" iconSize={8}
                  formatter={(value) => <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>No errors found 🎉</div>
          )}
        </div>

        <div className="glass-card" style={{ padding: 24 }}>
          <div className="section-header">
            <div>
              <div className="section-title">Country Error Breakdown</div>
              <div className="section-subtitle">Phone errors by country code</div>
            </div>
          </div>
          {barData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="country" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>No country errors</div>
          )}
        </div>
      </div>

      <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
        <div className="section-header">
          <div>
            <div className="section-title">Top Validation Failures</div>
            <div className="section-subtitle">Most frequent error codes</div>
          </div>
        </div>
        {topFailures.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Error Code</th>
                <th>Count</th>
                <th>% of Errors</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {topFailures.map((f, i) => (
                <tr key={f.code}>
                  <td style={{ color: "var(--text-muted)" }}>{i + 1}</td>
                  <td><code style={{ fontSize: 12, background: "rgba(99,102,241,0.1)", padding: "2px 8px", borderRadius: 4, color: "var(--accent)" }}>{f.code}</code></td>
                  <td style={{ fontWeight: 700 }}>{f.count.toLocaleString()}</td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div className="progress-bar-track" style={{ width: 80, height: 4 }}>
                        <div className="progress-bar-fill" style={{ width: `${f.pct}%` }} />
                      </div>
                      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{f.pct}%</span>
                    </div>
                  </td>
                  <td><span className="pill pill-error">ERROR</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 20 }}>No failures recorded</p>
        )}
      </div>
    </div>
  );
}

function Loader() {
  return (
    <div style={{ textAlign: "center", padding: 60 }}>
      <div style={{ fontSize: 32, marginBottom: 12 }} className="spin">⚙️</div>
      <p style={{ color: "var(--text-secondary)" }}>Loading dashboard…</p>
    </div>
  );
}
function ErrorMsg({ msg }: { msg: string }) {
  return (
    <div style={{ textAlign: "center", padding: 60, color: "#fca5a5" }}>❌ {msg}</div>
  );
}
