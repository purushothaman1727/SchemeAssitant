import axios from "axios";
import type { SchemeDetail } from "../types/api";

const http = axios.create({ baseURL: "/api/admin", timeout: 45000 });

const auth = (token: string) => ({ headers: { Authorization: `Bearer ${token}` } });

export interface SourceRow {
  id: number; scheme_id: string; url: string; title: string | null; source_type: string;
  verification_status: string; date_checked: string | null; notes: string | null;
  documents_ok: number; documents_failed: number; last_error: string | null;
}
export interface SourcePage { total: number; page: number; page_size: number; items: SourceRow[] }
export interface JobRow {
  id: number; scheme_id: string | null; status: string; documents_ok: number;
  documents_failed: number; errors: string[]; started_at: string; finished_at: string | null;
}
export interface SchemePatch {
  operational_status?: string;
  verification_status?: string;
  accepting_applications?: boolean | null;
  date_checked?: string | null;
  verification_notes?: string | null;
  benefits?: string | null;
}

export const login = (username: string, password: string) =>
  http.post<{ access_token: string; expires_in: number }>("/login", { username, password }).then((r) => r.data);

export const listSources = (token: string, page: number) =>
  http.get<SourcePage>("/sources", { ...auth(token), params: { page, page_size: 15 } }).then((r) => r.data);

export const listJobs = (token: string) =>
  http.get<JobRow[]>("/ingestion-jobs", auth(token)).then((r) => r.data);

export const startIngest = (token: string, schemeId: string | null) =>
  http.post("/ingest", { scheme_id: schemeId }, auth(token)).then((r) => r.data);

export const patchScheme = (token: string, id: string, body: SchemePatch) =>
  http.patch<SchemeDetail>(`/schemes/${encodeURIComponent(id)}`, body, auth(token)).then((r) => r.data);
