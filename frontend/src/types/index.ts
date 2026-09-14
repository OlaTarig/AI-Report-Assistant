export interface Conversation {
  id: string;
  title: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface UploadedFile {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export interface ReportTable {
  headers: string[];
  rows: string[][];
}

export interface ReportSection {
  id: string;
  heading: string;
  body: string;
  table?: ReportTable | null;
  image_file_ids: string[];
}

export interface ReportOut {
  title: string;
  sections: ReportSection[];
  version_number: number;
}
