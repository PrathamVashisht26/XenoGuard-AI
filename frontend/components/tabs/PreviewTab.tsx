"use client";

import { useState, useEffect } from "react";
import { getPreview } from "@/lib/api";
import type { PreviewData } from "@/types";

export default function PreviewTab({ sessionId }: { sessionId: string; status: string }) {
  const [data, setData] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPreview(sessionId).then((r) => { setData(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <Loader />;
  if (!data) return <p style={{ color: "var(--text-muted)", textAlign: "center", padding: 40 }}>Could not load preview.</p>;

  return (
    <div className="animate-fade-in-up">
      <div className="section-header">
        <div>
          <div className="section-title">File Preview</div>
          <div className="section-subtitle">First {data.count} rows · {data.headers.length} columns</div>
        </div>
        <span className="pill pill-info">{data.count} rows shown</span>
      </div>
      <div className="glass-card" style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 50 }}>#</th>
              {data.headers.map((h) => <th key={h}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i}>
                <td style={{ color: "var(--text-muted)" }}>{i + 1}</td>
                {data.headers.map((h) => (
                  <td key={h} style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {row[h] || <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>—</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
function Loader() { return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>Loading preview…</div>; }
