import { apiFetch } from "./client";
import type { Conversation, ConversationDetail } from "../types";

export function listConversations(): Promise<Conversation[]> {
  return apiFetch("/conversations");
}

export function createConversation(title = "New Report"): Promise<Conversation> {
  return apiFetch("/conversations", { method: "POST", body: JSON.stringify({ title }) });
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return apiFetch(`/conversations/${id}`);
}

export function renameConversation(id: string, title: string): Promise<Conversation> {
  return apiFetch(`/conversations/${id}`, { method: "PATCH", body: JSON.stringify({ title }) });
}

export function deleteConversation(id: string): Promise<void> {
  return apiFetch(`/conversations/${id}`, { method: "DELETE" });
}
