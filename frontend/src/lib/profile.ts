export interface ProfileStats {
  document_count: number;
  ready_document_count: number;
  chat_session_count: number;
  message_count: number;
  quiz_count: number;
  quiz_attempt_count: number;
  average_quiz_score_pct: number | null;
  flashcard_deck_count: number;
}
