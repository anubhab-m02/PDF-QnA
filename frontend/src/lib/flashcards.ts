export interface FlashcardItem {
  id: number;
  term: string;
  definition: string;
  position: number;
}

export interface FlashcardDeck {
  id: number;
  document_id: number;
  title: string;
  created_at: string;
  flashcards: FlashcardItem[];
}
