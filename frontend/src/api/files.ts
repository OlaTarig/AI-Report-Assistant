import type { UploadedFile } from "../types";
import { ApiError } from "./client";

export async function uploadFile(conversationId: string, file: File): Promise<UploadedFile> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`/api/conversations/${conversationId}/files`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Upload failed: ${res.status}`, res.status);
  }
  return res.json();
}

export async function listFiles(conversationId: string): Promise<UploadedFile[]> {
  const res = await fetch(`/api/conversations/${conversationId}/files`);
  if (!res.ok) throw new ApiError("Failed to load files", res.status);
  return res.json();
}
