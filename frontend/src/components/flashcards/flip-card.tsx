"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

export function FlipCard({ term, definition }: { term: string; definition: string }) {
  const [flipped, setFlipped] = useState(false);

  function toggle() {
    setFlipped((f) => !f);
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={flipped}
      aria-label={`Flashcard: ${term}. Press Enter to reveal definition`}
      onClick={toggle}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggle();
        }
      }}
      className="min-h-[260px] w-full cursor-pointer select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      style={{ perspective: "1200px" }}
    >
      <div
        className={cn(
          "relative h-full min-h-[260px] w-full transition-transform duration-300 ease-in-out motion-reduce:transition-none",
          flipped && "motion-safe:[transform:rotateY(180deg)]"
        )}
        style={{ transformStyle: "preserve-3d" }}
      >
        <div
          className={cn(
            "absolute inset-0 flex items-center justify-center rounded-lg border bg-card p-6 text-center text-lg font-medium",
            "backface-hidden motion-reduce:transition-opacity motion-reduce:duration-200",
            flipped ? "motion-reduce:opacity-0" : "motion-reduce:opacity-100"
          )}
          style={{ backfaceVisibility: "hidden" }}
        >
          {term}
        </div>
        <div
          className={cn(
            "absolute inset-0 flex items-center justify-center rounded-lg border bg-card p-6 text-center text-sm text-card-foreground",
            "backface-hidden motion-reduce:absolute motion-reduce:transition-opacity motion-reduce:duration-200",
            flipped ? "motion-reduce:opacity-100" : "motion-reduce:opacity-0"
          )}
          style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
        >
          {definition}
        </div>
      </div>
    </div>
  );
}
