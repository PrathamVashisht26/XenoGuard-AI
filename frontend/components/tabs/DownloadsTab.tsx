"use client";

import { useState, useEffect } from "react";
import { getDownloads, getDownloadUrl } from "@/lib/api";
import type { OutputFile } from "@/types";

const FILE_META: Record<string, { icon: string; desc: string }> = {
  CLEANED_CSV:            { icon: "✅", desc: "Valid + auto-fixed rows ready for downstream processing" },
  INVALID_CSV:            { icon: "❌", desc: "All rows that failed validation, for manual review" },
  VALIDATION_REPORT_PDF:  { icon: "📄", desc: "Full validation summary with health score and insights" },
  ERROR_EXPLANATION_CSV:  { icon: "💡", desc: "Every error with plain-English explanation and fix suggestion" },
  AUDIT_LOG_JSON:         { icon: "🔍", desc: "Complete audit trail of all actions and timestamps" },
};

function formatBytes(b?: number): string {
  if (!b) return "—";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(2)} MB`;
}

export default function DownloadsTab({ sessionId, status }: { sessionId: string; status: string }) {
  const [files, setFiles] = useState<OutputFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status !== "COMPLETED") return;
    getDownloads(sessionId).then((r) => { setFiles(r.data.files); setLoading(false); }).catch(() => setLoading(false));
  }, [sessionId, status]);

  if (status !== "COMPLETED") return <Waiting />;
  if (loading) return <Loader />;

  return (
    <div className="animate-fade-in-up">
      <div className="section-header">
        <div>
          <div className="section-title">Download Center</div>
          <div className="section-subtitle">All output files generated for this session</div>
        </div>
      </div>

      {files.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <p style={{ color: "var(--text-muted)" }}>Output files are being generated…</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {files.map((file) => {
            const meta = FILE_META[file.file_type] || { icon: "📁", desc: "" };
            return (
              <div key={file.id} className="glass-card" style={{ padding: "20px 24px", display: "flex", alignItems: "center", gap: 20 }}>
                <div style={{ fontSize: 32 }}>{meta.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{file.display_name}</div>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>{meta.desc}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                    {formatBytes(file.file_size_bytes)}
                    {file.generated_at && ` · ${new Date(file.generated_at).toLocaleString()}`}
                  </div>
                </div>
                <a
                  href={getDownloadUrl(file.id)}
                  download={file.display_name}
                  className="btn-primary"
                  id={`download-${file.file_type.toLowerCase()}`}
                >
                  ⬇️ Download
                </a>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Waiting() { return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>⏳ Downloads available after processing completes.</div>; }
function Loader() { return <div style={{ textAlign: "center", padding: 60, color: "var(--text-secondary)" }}>Loading downloads…</div>; }
