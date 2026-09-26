import { useRef, useState } from "react";
import type { UploadedFile } from "../types";

interface Props {
  files: UploadedFile[];
  onUpload: (file: File) => Promise<void>;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({ files, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(fileList)) {
        await onUpload(file);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="border-t px-6 py-2">
      <div className="mx-auto flex max-w-2xl flex-wrap items-center gap-2">
        {files.map((f) => (
          <span
            key={f.id}
            className="flex items-center gap-1 rounded-full bg-brand-peach px-3 py-1 text-xs text-brand-orange-dark"
            title={formatSize(f.size_bytes)}
          >
            📎 {f.original_filename}
          </span>
        ))}

        <button
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="rounded-full border border-dashed border-gray-300 px-3 py-1 text-xs text-gray-500 hover:border-brand-orange hover:text-brand-orange disabled:opacity-50"
        >
          {uploading ? "Uploading…" : "+ Attach file"}
        </button>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.xlsx,.xls,.png,.jpg,.jpeg,.webp"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />

        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    </div>
  );
}
