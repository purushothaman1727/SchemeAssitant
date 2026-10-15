import axios, { AxiosError } from "axios";
import type {
  ChatReply, ProfilePayload, RecommendationResponse, SchemeDetail, SchemePage,
} from "../types/api";


const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : "/api",
  timeout: 45000,
});


export function errorMessage(e: unknown): string {
  const err = e as AxiosError<{ detail?: unknown }>;
  if (err.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (!err.response) return "Cannot reach the server. Check your connection and try again.";
  if (err.response.status === 422) return "Some of the details are not valid. Please check the form.";
  if (err.response.status === 429) return "Too many requests. Please wait a moment and try again.";
  if (err.response.status >= 500) return "The service had a problem. Please try again shortly.";
  const d = err.response.data?.detail;
  return typeof d === "string" ? d : "Something went wrong.";
}

export const getRecommendations = (profile: ProfilePayload) =>
  http.post<RecommendationResponse>("/recommendations", { profile }).then((r) => r.data);

export const listSchemes = (params: Record<string, string | number | undefined>) =>
  http.get<SchemePage>("/schemes", { params }).then((r) => r.data);

export const getScheme = (id: string) =>
  http.get<SchemeDetail>(`/schemes/${encodeURIComponent(id)}`).then((r) => r.data);

export interface ChatTurn { role: "user" | "assistant"; content: string }

export const sendChat = (body: {
  message: string;
  language: "en" | "ta" | "auto";
  profile: ProfilePayload | null;
  history: ChatTurn[];
  store_history: boolean;
  session_id: string | null;
}) => http.post<ChatReply>("/chat", body).then((r) => r.data);

export const deleteChatSession = (id: string) => http.delete(`/chat/sessions/${id}`);
