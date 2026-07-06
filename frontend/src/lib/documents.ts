export interface Document {
  id: number;
  filename: string;
  title: string;
  page_count: number;
  chunk_count: number;
  status: "processing" | "ready" | "failed";
  error: string | null;
  created_at: string;
}
