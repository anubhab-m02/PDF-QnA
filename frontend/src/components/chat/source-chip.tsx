"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Source } from "@/lib/chat";

export function SourceChip({ source }: { source: Source }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-full bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground hover:bg-accent"
      >
        p. {source.page ?? "?"}
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Source — page {source.page ?? "?"}</DialogTitle>
            <DialogDescription className="whitespace-pre-wrap text-left">
              {source.text}
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </>
  );
}
