import { useEffect, useState } from "react";
import * as conversationsApi from "../api/conversations";
import * as filesApi from "../api/files";
import type { Conversation } from "../types";

const SHARE_CACHE = "share-target-cache";

async function readDebugLog(): Promise<Record<string, unknown> | null> {
  const cache = await caches.open(SHARE_CACHE);
  const response = await cache.match("share-debug");
  if (!response) return null;
  return response.json();
}

async function readSharedFiles(retries = 5): Promise<File[]> {
  for (let attempt = 0; attempt < retries; attempt++) {
    const cache = await caches.open(SHARE_CACHE);
    const metaResponse = await cache.match("share-meta");

    if (metaResponse) {
      const { count } = await metaResponse.json();
      const files: File[] = [];

      for (let i = 0; i < count; i++) {
        const response = await cache.match(`share-file-${i}`);
        if (!response) continue;
        const blob = await response.blob();
        const name = decodeURIComponent(response.headers.get("X-File-Name") || `shared-file-${i}`);
        files.push(new File([blob], name, { type: blob.type }));
      }

      await cache.delete("share-meta");
      await cache.delete("share-debug");
      for (let i = 0; i < count; i++) await cache.delete(`share-file-${i}`);

      return files;
    }

    await new Promise((res) => setTimeout(res, 200));
  }

  return [];
}

export default function ShareTargetHandler() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [sharedFiles, setSharedFiles] = useState<File[]>([]);
  const [debugLog, setDebugLog] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const log = await readDebugLog();
      const [convList, files] = await Promise.all([
        conversationsApi.listConversations(),
        readSharedFiles(),
      ]);
      setConversations(convList);
      setSharedFiles(files);
      setDebugLog(log);
      setLoading(false);
    }
    loadData();
  }, []);

  async function uploadTo(conversationId: string) {
    setUploading(true);
    setError(null);
    try {
      for (const file of sharedFiles) {
        await filesApi.uploadFile(conversationId, file);
      }
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setUploading(false);
    }
  }

  async function createAndUpload() {
    try {
      const conversation = await conversationsApi.createConversation();
      await uploadTo(conversation.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create conversation.");
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-brand-offwhite text-gray-500">
        Loading shared files…
      </div>
    );
  }

  if (sharedFiles.length === 0 && !uploading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-brand-offwhite px-6 text-center">
        <p className="text-gray-500">No shared file found.</p>
        {debugLog ? (
          <pre className="max-w-full overflow-x-auto rounded bg-brand-white p-3 text-left text-xs text-gray-600">
            {JSON.stringify(debugLog, null, 2)}
          </pre>
        ) : (
          <p className="text-xs text-gray-400">
            (No debug log found either — the service worker may not have intercepted this request
            at all.)
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-brand-offwhite px-6">
      <p className="text-center text-gray-700">
        Add {sharedFiles.map((f) => f.name).join(", ")} to which report?
      </p>

      {uploading ? (
        <p className="text-sm text-gray-400">Uploading…</p>
      ) : (
        <div className="flex w-full max-w-sm flex-col gap-2">
          <button
            onClick={createAndUpload}
            className="rounded-lg bg-brand-orange-muted px-4 py-2 text-sm font-medium text-white hover:bg-brand-orange-dark"
          >
            + New Report
          </button>
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => uploadTo(c.id)}
              className="rounded-lg border border-gray-300 bg-brand-white px-4 py-2 text-left text-sm text-gray-700 hover:bg-brand-peach"
            >
              {c.title}
            </button>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}