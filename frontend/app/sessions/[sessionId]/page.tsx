"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getSession } from "@/lib/api";
import type { Session, SSEPayload } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

const NAV_TABS = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "preview", label: "Preview", icon: "👁️" },
  { id: "validation", label: "Validation", icon: "🔍" },
  { id: "fix-studio", label: "Fix Studio", icon: "🛠️" },
  { id: "insights", label: "AI Insights", icon: "💡" },
  { id: "downloads", label: "Downloads", icon: "⬇️" },
  { id: "audit", label: "Audit Trail", icon: "📋" },
];

export default function SessionLayout() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [ssePayload, setSsePayload] = useState<SSEPayload | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getSession(sessionId).then((r) => setSession(r.data)).catch(() => {});
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;
    const es = new EventSource(`${API_BASE}/events/${sessionId}`);
    es.onmessage = (e) => {
      const payload: SSEPayload = JSON.parse(e.data);
      setSsePayload(payload);
      if (payload.status === "COMPLETED" || payload.status === "FAILED") {
        es.close();
        getSession(sessionId).then((r) => setSession(r.data)).catch(() => {});
      }
    };
    return () => es.close();
  }, [sessionId]);

  const status = ssePayload?.status || session?.status || "PENDING";
  const isProcessing = status === "PROCESSING" || status === "PENDING";
  const progressPct = ssePayload?.progress_pct ?? 0;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      <nav style={{
        borderBottom: "1px solid var(--border)",
        background: "rgba(10,11,20,0.85)",
        backdropFilter: "blur(12px)",
        position: "sticky", top: 0, zIndex: 50,
      }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", padding: "0 24px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, height: 56 }}>
            <button
              onClick={() => router.push("/")}
              style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", fontSize: 18 }}
              title="Back to upload"
            >←</button>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 16, fontWeight: 800 }}>
                <span className="gradient-text">XenoGuard</span>
                <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> AI</span>
              </span>
            </div>
            <span style={{ color: "var(--text-muted)", margin: "0 4px" }}>/</span>
            <span style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "monospace" }}>
              {sessionId?.slice(0, 8)}…
            </span>
            {session && (
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
                · {session.original_name}
              </span>
            )}
            <div style={{ marginLeft: "auto" }}>
              <StatusPill status={status} />
            </div>
          </div>
        </div>
      </nav>

      {isProcessing && (
        <div style={{
          background: "rgba(99,102,241,0.08)",
          borderBottom: "1px solid rgba(99,102,241,0.2)",
          padding: "12px 24px",
        }}>
          <div style={{ maxWidth: 1280, margin: "0 auto" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: "var(--accent)" }}>
                ⚙️ Processing {ssePayload?.done_chunks ?? 0} / {ssePayload?.total_chunks ?? "?"} chunks
              </span>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{progressPct}%</span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        </div>
      )}

      <div style={{
        borderBottom: "1px solid var(--border)",
        background: "var(--bg-secondary)",
        overflowX: "auto",
      }}>
        <div style={{
          maxWidth: 1280, margin: "0 auto", padding: "0 24px",
          display: "flex", gap: 4, overflowX: "auto",
        }}>
          {NAV_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`nav-tab ${activeTab === tab.id ? "active" : ""}`}
              style={{ whiteSpace: "nowrap", padding: "12px 16px" }}
              id={`tab-${tab.id}`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px" }}>
        <TabContent sessionId={sessionId} activeTab={activeTab} status={status} />
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, { cls: string; dot: string; label: string }> = {
    PENDING:    { cls: "pill-pending",    dot: "⬤", label: "Pending" },
    PROCESSING: { cls: "pill-processing", dot: "⬤", label: "Processing" },
    COMPLETED:  { cls: "pill-completed",  dot: "⬤", label: "Completed" },
    FAILED:     { cls: "pill-failed",     dot: "⬤", label: "Failed" },
  };
  const { cls, dot, label } = map[status] || map.PENDING;
  return <span className={`pill ${cls}`}>{dot} {label}</span>;
}

import dynamic from "next/dynamic";

const DashboardTab    = dynamic(() => import("@/components/tabs/DashboardTab"));
const PreviewTab      = dynamic(() => import("@/components/tabs/PreviewTab"));
const ValidationTab   = dynamic(() => import("@/components/tabs/ValidationTab"));
const FixStudioTab    = dynamic(() => import("@/components/tabs/FixStudioTab"));
const InsightsTab     = dynamic(() => import("@/components/tabs/InsightsTab"));
const DownloadsTab    = dynamic(() => import("@/components/tabs/DownloadsTab"));
const AuditTab        = dynamic(() => import("@/components/tabs/AuditTab"));

function TabContent({ sessionId, activeTab, status }: { sessionId: string; activeTab: string; status: string }) {
  const props = { sessionId, status };
  switch (activeTab) {
    case "dashboard":    return <DashboardTab {...props} />;
    case "preview":      return <PreviewTab {...props} />;
    case "validation":   return <ValidationTab {...props} />;
    case "fix-studio":   return <FixStudioTab {...props} />;
    case "insights":     return <InsightsTab {...props} />;
    case "downloads":    return <DownloadsTab {...props} />;
    case "audit":        return <AuditTab {...props} />;
    default:             return <DashboardTab {...props} />;
  }
}
