"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { uploadFile } from "@/lib/api";

const MAX_SIZE_MB = 100;

export default function HomePage() {
  const router = useRouter();
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    if (!file.name.endsWith(".csv")) {
      setError("Only CSV files are accepted.");
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File must be under ${MAX_SIZE_MB}MB.`);
      return;
    }
    setUploading(true);
    try {
      const res = await uploadFile(file, setProgress);
      const { session_id } = res.data;
      router.push(`/sessions/${session_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Upload failed. Ensure the backend is running.");
      setUploading(false);
    }
  }, [router]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      <nav style={{
        borderBottom: "1px solid var(--border)",
        background: "rgba(10,11,20,0.8)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}>
        <div className="page-container" style={{ padding: "14px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: "linear-gradient(135deg, #6366f1, #a78bfa)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 18, fontWeight: 900
            }}>𝕏</div>
            <span style={{ fontSize: 18, fontWeight: 800 }}>
              <span className="gradient-text">XenoGuard</span>
              <span style={{ color: "var(--text-secondary)", fontWeight: 400, marginLeft: 4 }}>AI</span>
            </span>
          </div>
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace" }}>v1.0.0</span>
            <span className="pill pill-info">🌍 10 Countries Supported</span>
          </div>
        </div>
      </nav>

      <div className="page-container" style={{ paddingTop: 80, paddingBottom: 60, textAlign: "center" }}>
        <div className="animate-fade-in-up">
          <span className="pill pill-info" style={{ marginBottom: 20, display: "inline-flex" }}>
            🤖 AI-Powered Transaction Recovery
          </span>
          <h1 style={{ fontSize: 56, fontWeight: 900, lineHeight: 1.1, marginBottom: 20 }}>
            <span className="gradient-text">Validate. Explain. Fix.</span>
            <br />
            <span style={{ color: "var(--text-primary)" }}>Your Transaction Data.</span>
          </h1>
          <p style={{ fontSize: 18, color: "var(--text-secondary)", maxWidth: 620, margin: "0 auto 48px", lineHeight: 1.7 }}>
            Upload international transaction CSVs. XenoGuard AI validates every row, explains each error in plain English,
            and automatically suggests fixes — so your data is production-ready.
          </p>
        </div>

        <div
          className={`dropzone ${dragActive ? "active" : ""} animate-fade-in-up`}
          style={{ maxWidth: 680, margin: "0 auto", animationDelay: "0.1s" }}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={onDrop}
          onClick={() => !uploading && inputRef.current?.click()}
          id="upload-dropzone"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={onInputChange}
            id="file-input"
          />
          <div className="dropzone-inner">
            {uploading ? (
              <>
                <div style={{ fontSize: 48, marginBottom: 8 }}>⚙️</div>
                <p style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
                  Uploading & Processing…
                </p>
                <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 20 }}>
                  {progress < 100 ? `Uploading: ${progress}%` : "Starting validation pipeline…"}
                </p>
                <div className="progress-bar-track" style={{ width: 300 }}>
                  <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
                </div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 56 }}>📂</div>
                <p style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
                  Drop your CSV here
                </p>
                <p style={{ fontSize: 14, color: "var(--text-secondary)" }}>
                  or <span style={{ color: "var(--accent)", fontWeight: 600 }}>click to browse</span>
                  {" "}· CSV only · Up to 100MB
                </p>
                <button className="btn-primary" style={{ marginTop: 8 }}>
                  📁 Select File
                </button>
              </>
            )}
          </div>
        </div>

        {error && (
          <div style={{
            marginTop: 16, padding: "12px 20px", background: "rgba(239,68,68,0.1)",
            border: "1px solid rgba(239,68,68,0.3)", borderRadius: 10,
            color: "#fca5a5", fontSize: 14, maxWidth: 680, margin: "16px auto 0"
          }}>
            ⚠️ {error}
          </div>
        )}

        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "center", marginTop: 40 }}>
          {[
            "🌍 Country-Aware Phone Validation",
            "📅 Multi-Format Date Parsing",
            "🔍 Duplicate Detection",
            "💡 Plain-English Explanations",
            "🛠️ AI Auto-Fix Studio",
            "📊 Health Score Dashboard",
            "📄 PDF Report Export",
            "⚡ Async Chunk Processing",
          ].map((f) => (
            <span key={f} className="pill pill-info" style={{ padding: "6px 14px", fontSize: 13 }}>{f}</span>
          ))}
        </div>
      </div>

      <div style={{ borderTop: "1px solid var(--border)", padding: "60px 24px" }}>
        <div className="page-container">
          <h2 style={{ textAlign: "center", fontSize: 28, fontWeight: 800, marginBottom: 40 }}>
            How <span className="gradient-text">XenoGuard</span> Works
          </h2>
          <div className="grid-4">
            {[
              { icon: "📤", step: "01", title: "Upload CSV", desc: "Drag & drop your transaction dataset. Files up to 100MB are accepted and chunked automatically." },
              { icon: "🤖", step: "02", title: "AI Validation", desc: "9 validation engines run in parallel — phone, date, email, payment, currency, duplicates, and more." },
              { icon: "💡", step: "03", title: "Explain & Fix", desc: "Every error gets a plain-English diagnosis and a one-click fix suggestion in the Fix Studio." },
              { icon: "⬇️", step: "04", title: "Download", desc: "Export cleaned CSV, invalid records, PDF report, error explanations, and audit log." },
            ].map((item) => (
              <div key={item.step} className="glass-card" style={{ padding: "28px 24px", textAlign: "center" }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>{item.icon}</div>
                <div style={{ fontSize: 11, color: "var(--accent)", fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8 }}>
                  STEP {item.step}
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>{item.title}</h3>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <footer style={{
        borderTop: "1px solid var(--border)",
        padding: "24px",
        textAlign: "center",
        color: "var(--text-muted)",
        fontSize: 13,
      }}>
        XenoGuard AI · Built with FastAPI + Next.js · Powered by Celery + Redis
      </footer>
    </div>
  );
}
