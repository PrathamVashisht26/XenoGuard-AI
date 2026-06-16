import axios from "axios";

const IS_PROD = typeof window !== "undefined" && !window.location.hostname.includes("localhost");
const API_BASE = process.env.NEXT_PUBLIC_API_URL || (IS_PROD ? "https://xenoguard-ai.onrender.com/v1" : "http://localhost:8000/v1");

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const uploadFile = (file: File, onProgress?: (pct: number) => void) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
};

export const getSession = (id: string) => api.get(`/sessions/${id}`);
export const getPreview = (id: string) => api.get(`/sessions/${id}/preview`);
export const getSummary = (id: string) => api.get(`/sessions/${id}/summary`);
export const getTransactions = (id: string, page = 1, filter = "all") =>
  api.get(`/sessions/${id}/transactions?page=${page}&filter=${filter}`);
export const getErrors = (id: string, txnId?: number, page = 1) =>
  api.get(`/sessions/${id}/errors${txnId ? `?transaction_id=${txnId}&page=${page}` : `?page=${page}`}`);
export const getInsights = (id: string) => api.get(`/sessions/${id}/insights`);
export const getAudit = (id: string) => api.get(`/sessions/${id}/audit`);
export const getDownloads = (id: string) => api.get(`/sessions/${id}/downloads`);

export const acceptFix = (errorId: number) => api.patch(`/fixes/${errorId}/accept`);
export const acceptAllFixes = (sessionId: string) =>
  api.post(`/sessions/${sessionId}/fixes/accept-all`);

export const getDownloadUrl = (fileId: string) =>
  `${API_BASE}/downloads/${fileId}`;
