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

/** Retrieval can return multiple chunks from the same page — merge those into a
 * single chip (with all their snippets joined) rather than showing duplicate
 * "p. N" chips for one page. */
export function dedupeSourcesByPage(sources: Source[]): Source[] {
  const byPage = new Map<string, Source>();
  for (const source of sources) {
    const key = String(source.page ?? "unknown");
    const existing = byPage.get(key);
    if (existing) {
      existing.text += "\n\n---\n\n" + source.text;
    } else {
      byPage.set(key, { ...source });
    }
  }
  return Array.from(byPage.values());
}
