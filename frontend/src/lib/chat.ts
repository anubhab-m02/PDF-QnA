export interface ChatSession {
  id: number;
  document_id: number | null;
  title: string;
  created_at: string;
}

export interface Source {
  text: string;
  page?: number;
  document_id?: number;
  user_id?: number;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources_json: string | null;
  created_at: string;
}

export function parseSources(sourcesJson: string | null): Source[] {
  if (!sourcesJson) return [];
  try {
    return JSON.parse(sourcesJson) as Source[];
  } catch {
    return [];
  }
}
