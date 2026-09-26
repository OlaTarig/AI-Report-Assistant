import { useState } from "react";
import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
  onRename,
  onDelete,
}: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  function startRename(c: Conversation) {
    setEditingId(c.id);
    setEditTitle(c.title);
  }

  function commitRename() {
    if (editingId && editTitle.trim()) {
      onRename(editingId, editTitle.trim());
    }
    setEditingId(null);
  }

  return (
    <div className="flex h-full flex-col border-r bg-brand-white">
      <div className="border-b p-3">
        <button
          onClick={onNew}
          className="w-full rounded-lg bg-brand-orange px-3 py-2 text-sm font-medium text-white hover:bg-brand-orange-dark"
        >
          + New Report
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 && (
          <p className="p-4 text-sm text-gray-400">No reports yet.</p>
        )}

        {conversations.map((c) => (
          <div
            key={c.id}
            onClick={() => editingId !== c.id && onSelect(c.id)}
            className={`group flex cursor-pointer items-center justify-between border-b px-3 py-2 text-sm ${
              c.id === activeId ? "bg-brand-peach" : "hover:bg-brand-offwhite"
            }`}
          >
            {editingId === c.id ? (
              <input
                autoFocus
                className="w-full rounded border px-1 py-0.5 text-sm outline-none"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onBlur={commitRename}
                onKeyDown={(e) => e.key === "Enter" && commitRename()}
              />
            ) : (
              <>
                <span className="truncate text-gray-700">{c.title}</span>
                <div className="hidden gap-1 group-hover:flex">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startRename(c);
                    }}
                    className="text-xs text-gray-400 hover:text-gray-600"
                    title="Rename"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete "${c.title}"?`)) onDelete(c.id);
                    }}
                    className="text-xs text-gray-400 hover:text-red-500"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
