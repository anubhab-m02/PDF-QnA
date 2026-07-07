"use client";

import { use, useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { DocumentNav } from "@/components/documents/document-nav";
import { FlipCard } from "@/components/flashcards/flip-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, authHeaders, ApiError, NetworkError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FlashcardDeck } from "@/lib/flashcards";

export default function DocumentFlashcardsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const documentId = Number(id);
  const { token } = useAuth();

  const [decks, setDecks] = useState<FlashcardDeck[] | null>(null);
  const [activeDeckId, setActiveDeckId] = useState<number | null>(null);
  const [cardIndex, setCardIndex] = useState(0);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!token || Number.isNaN(documentId)) return;
    (async () => {
      try {
        const list = await apiFetch<FlashcardDeck[]>(
          `/api/flashcard-decks?document_id=${documentId}`,
          { headers: authHeaders(token) }
        );
        setDecks(list);
        if (list.length > 0) setActiveDeckId(list[0].id);
      } catch (err) {
        if (err instanceof ApiError || err instanceof NetworkError) toast.error(err.message);
      }
    })();
  }, [token, documentId]);

  async function generateDeck() {
    if (!token) return;
    setGenerating(true);
    try {
      const deck = await apiFetch<FlashcardDeck>(`/api/documents/${documentId}/flashcards`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ num_cards: 10 }),
      });
      setDecks((prev) => [deck, ...(prev ?? [])]);
      setActiveDeckId(deck.id);
      setCardIndex(0);
    } catch (err) {
      if (err instanceof ApiError || err instanceof NetworkError) {
        toast.error(err.message);
      } else {
        toast.error("Failed to generate flashcards");
      }
    } finally {
      setGenerating(false);
    }
  }

  const activeDeck = decks?.find((d) => d.id === activeDeckId) ?? null;
  const card = activeDeck?.flashcards[cardIndex];

  const goPrev = useCallback(() => {
    setCardIndex((i) => Math.max(0, i - 1));
  }, []);
  const goNext = useCallback(() => {
    setCardIndex((i) => (activeDeck ? Math.min(activeDeck.flashcards.length - 1, i + 1) : i));
  }, [activeDeck]);

  useEffect(() => {
    if (!activeDeck) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "ArrowLeft") goPrev();
      if (e.key === "ArrowRight") goNext();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeDeck, goPrev, goNext]);

  return (
    <div className="h-full overflow-y-auto">
      <DocumentNav documentId={documentId} />
      <div className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-8">
        {decks === null && (
          <div className="flex flex-col gap-3 pt-4">
            <Skeleton className="h-64 rounded-lg" />
          </div>
        )}

        {decks !== null && !activeDeck && (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <p className="text-lg font-medium">No flashcards yet</p>
            <p className="text-sm text-muted-foreground">
              Generate a deck from this document to start studying
            </p>
            <Button onClick={generateDeck} disabled={generating}>
              {generating ? "Generating…" : "Generate flashcards"}
            </Button>
          </div>
        )}

        {activeDeck && card && (
          <div className="flex flex-col items-center gap-4">
            <FlipCard key={card.id} term={card.term} definition={card.definition} />

            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="icon"
                aria-label="Previous card"
                disabled={cardIndex === 0}
                onClick={goPrev}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                {cardIndex + 1} / {activeDeck.flashcards.length}
              </span>
              <Button
                variant="outline"
                size="icon"
                aria-label="Next card"
                disabled={cardIndex === activeDeck.flashcards.length - 1}
                onClick={goNext}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>

            <Button variant="outline" size="sm" onClick={generateDeck} disabled={generating}>
              {generating ? "Generating…" : "Generate new deck"}
            </Button>
          </div>
        )}

        {decks && decks.length > 1 && (
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium text-muted-foreground">Decks</p>
            <div className="flex flex-col divide-y rounded-md border">
              {decks.map((deck) => (
                <button
                  key={deck.id}
                  type="button"
                  onClick={() => {
                    setActiveDeckId(deck.id);
                    setCardIndex(0);
                  }}
                  className="flex items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent/50"
                >
                  <span>{deck.title || `Deck · ${deck.flashcards.length} cards`}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(deck.created_at).toLocaleDateString()}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
