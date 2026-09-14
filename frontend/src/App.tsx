import { useEffect, useState } from "react";
import ConversationList from "./components/ConversationList";
import ChatPanel from "./components/ChatPanel";
import FileUpload from "./components/FileUpload";
import * as conversationsApi from "./api/conversations";
import * as messagesApi from "./api/messages";
import * as filesApi from "./api/files";
import type { Conversation, ConversationDetail, UploadedFile } from "./types";

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Load the sidebar list once on mount.
  useEffect(() => {
    conversationsApi.listConversations().then(setConversations);
  }, []);

  // Whenever the active conversation changes, load its messages + files.
  useEffect(() => {
    if (!activeId) {
      setActiveConversation(null);
      setFiles([]);
      return;
    }
    conversationsApi.getConversation(activeId).then(setActiveConversation);
    filesApi.listFiles(activeId).then(setFiles);
  }, [activeId]);

  async function handleNew() {
    const conversation = await conversationsApi.createConversation();
    setConversations((prev) => [conversation, ...prev]);
    setActiveId(conversation.id);
  }

  async function handleRename(id: string, title: string) {
    const updated = await conversationsApi.renameConversation(id, title);
    setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)));
  }

  async function handleDelete(id: string) {
    await conversationsApi.deleteConversation(id);
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) setActiveId(null);
  }

  async function handleSend(content: string) {
    if (!activeId) return;

    // Show the user's message immediately, before the AI call even starts,
    // so sending never looks like it silently did nothing.
    const tempId = `temp-${Date.now()}`;
    setActiveConversation((prev) =>
      prev
        ? {
            ...prev,
            messages: [
              ...prev.messages,
              { id: tempId, role: "user", content, created_at: new Date().toISOString() },
            ],
          }
        : prev
    );

    setLoading(true);
    setError(null);
    const controller = new AbortController();
    setAbortController(controller);

    try {
      const [userMsg, assistantMsg] = await messagesApi.sendMessage(activeId, content, controller.signal);
      setActiveConversation((prev) =>
        prev
          ? { ...prev, messages: [...prev.messages.filter((m) => m.id !== tempId), userMsg, assistantMsg] }
          : prev
      );
      // Sending a message updates the conversation's updated_at server-side —
      // refresh the sidebar list so it re-sorts to reflect that.
      conversationsApi.listConversations().then(setConversations);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setActiveConversation((prev) =>
          prev ? { ...prev, messages: prev.messages.filter((m) => m.id !== tempId) } : prev
        );
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong.");
      }
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  }

  function handleStop() {
    abortController?.abort();
  }

  async function handleUpload(file: File) {
    if (!activeId) return;
    const uploaded = await filesApi.uploadFile(activeId, file);
    setFiles((prev) => [...prev, uploaded]);
  }

  function handleExport() {
    if (!activeId) return;
    window.open(`/api/conversations/${activeId}/report/export`, "_blank");
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="w-64 flex-shrink-0">
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={handleNew}
          onRename={handleRename}
          onDelete={handleDelete}
        />
      </div>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-white px-6 py-3">
          <h1 className="text-lg font-semibold text-gray-800">
            {activeConversation?.title ?? "AI Report Assistant"}
          </h1>
          {activeId && (
            <button
              onClick={handleExport}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
            >
              Download Word
            </button>
          )}
        </header>

        {activeId ? (
          <>
            <div className="flex-1 overflow-hidden">
              <ChatPanel
                messages={activeConversation?.messages ?? []}
                onSend={handleSend}
                onStop={handleStop}
                loading={loading}
                error={error}
              />
            </div>
            <FileUpload files={files} onUpload={handleUpload} />
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center text-gray-400">
            Select a report or start a new one.
          </div>
        )}
      </div>
    </div>
  );
}
