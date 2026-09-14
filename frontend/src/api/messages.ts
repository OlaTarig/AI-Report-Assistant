import { apiFetch } from "./client";
import type { Message } from "../types";

export function sendMessage(
  conversationId: string,
  content: string,
  signal?: AbortSignal
): Promise<Message[]> {
  return apiFetch(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
    signal,
  });
}
