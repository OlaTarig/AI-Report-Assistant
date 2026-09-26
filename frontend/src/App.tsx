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
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    conversationsApi.listConversations().then(setConversations);
  }, []);

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
    setSidebarOpen(false); // on mobile, picking/creating a conversation should close the drawer
  }

  function handleSelect(id: string) {
    setActiveId(id);
    setSidebarOpen(false);
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

  function handleExportWord() {
    if (!activeId) return;
    window.open(`/api/conversations/${activeId}/report/export`, "_blank");
  }

  function handleExportPdf() {
    if (!activeId) return;
    window.open(`/api/conversations/${activeId}/report/export/pdf`, "_blank");
  }

  return (
    <div className="flex h-screen bg-brand-offwhite">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 flex-shrink-0 transform transition-transform duration-200 ease-in-out md:relative md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelect}
          onNew={handleNew}
          onRename={handleRename}
          onDelete={handleDelete}
        />
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between gap-2 border-b bg-brand-white px-4 py-3 md:px-6">
          <div className="flex min-w-0 items-center gap-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded p-1 text-gray-500 hover:bg-brand-peach md:hidden"
              aria-label="Open conversation list"
            >
              ☰
            </button>
            <h1 className="truncate text-base font-semibold text-gray-800 md:text-lg">
              {activeConversation?.title ?? "AI Report Assistant"}
            </h1>
          </div>
          {activeId && (
            <div className="flex flex-shrink-0 gap-2">
              <button
                onClick={handleExportWord}
                className="rounded-lg border border-gray-300 px-2 py-1.5 text-xs text-gray-600 hover:bg-brand-peach md:px-3 md:text-sm"
              >
                Word
              </button>
              <button
                onClick={handleExportPdf}
                className="rounded-lg border border-gray-300 px-2 py-1.5 text-xs text-gray-600 hover:bg-brand-peach md:px-3 md:text-sm"
              >
                PDF
              </button>
            </div>
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
          <div className="flex flex-1 items-center justify-center px-4 text-center text-gray-400">
            Select a report or start a new one.
          </div>
        )}
      </div>
    </div>
  );
}