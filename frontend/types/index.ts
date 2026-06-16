// Shared TypeScript types for XenoGuard AI

export interface Session {
  session_id: string;
  original_name: string;
  file_size_bytes: number;
  total_rows: number;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  uploaded_at: string;
  completed_at?: string;
  total_chunks: number;
  done_chunks: number;
}

export interface SSEPayload {
  session_id: string;
  status: string;
  total_rows: number;
  total_chunks: number;
  done_chunks: number;
  failed_chunks: number;
  progress_pct: number;
}

export interface ValidationSummary {
  session_id: string;
  health_score: number;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  fixed_rows: number;
  error_breakdown: Record<string, number>;
  country_breakdown: Record<string, number>;
  top_failures: Array<{ code: string; count: number; pct: number }>;
  ai_insights: Insight[];
  generated_at: string;
}

export interface Insight {
  severity: "INFO" | "WARNING" | "CRITICAL";
  title: string;
  body: string;
  affected_count: number;
}

export interface Transaction {
  id: number;
  row_number: number;
  is_valid: boolean;
  is_fixed: boolean;
  data: Record<string, string>;
  error_count: number;
}

export interface ValidationError {
  id: number;
  transaction_id: number;
  field_name?: string;
  error_code: string;
  error_category: string;
  severity: "ERROR" | "WARNING";
  raw_value?: string;
  explanation?: string;
  fix_suggestion?: string;
  fix_action?: string;
  fix_accepted: boolean;
}

export interface OutputFile {
  id: string;
  file_type: string;
  display_name: string;
  file_size_bytes?: number;
  generated_at?: string;
}

export interface AuditEvent {
  event_type: string;
  actor: string;
  occurred_at: string;
  event_data?: Record<string, unknown>;
}

export interface PreviewData {
  headers: string[];
  rows: Record<string, string>[];
  count: number;
}
