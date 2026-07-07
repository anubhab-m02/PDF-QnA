export interface QuizQuestion {
  question: string;
  options: string[];
  answer_index: number;
  explanation: string;
}

export interface Quiz {
  id: number;
  document_id: number;
  topic: string;
  questions: QuizQuestion[];
  created_at: string;
}

export interface QuizAttempt {
  id: number;
  quiz_id: number;
  answers: number[];
  score: number;
  total: number;
  created_at: string;
}

export function scoreTier(pct: number): "high" | "mid" | "low" {
  if (pct >= 80) return "high";
  if (pct >= 50) return "mid";
  return "low";
}
