"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, MoreVertical, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { StatusBadge } from "@/components/library/status-badge";
import type { Document } from "@/lib/documents";

export function DocumentCard({
  document,
  onDelete,
}: {
  document: Document;
  onDelete: (id: number) => Promise<void>;
}) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const router = useRouter();

  async function handleConfirmDelete() {
    setDeleting(true);
    try {
      await onDelete(document.id);
      setConfirmOpen(false);
    } finally {
      setDeleting(false);
    }
  }

  function handleClick() {
    if (document.status === "ready") {
      router.push(`/documents/${document.id}/chat`);
    }
  }

  const card = (
    <Card
      role={document.status === "ready" ? "button" : undefined}
      tabIndex={document.status === "ready" ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={(e) => {
        if (document.status === "ready" && (e.key === "Enter" || e.key === " ")) handleClick();
      }}
      className={
        "min-w-0 gap-3 p-4 transition-all duration-150 ease-out" +
        (document.status === "ready" ? " cursor-pointer hover:-translate-y-0.5 hover:shadow-md" : "")
      }
    >
      <div className="flex items-start justify-between gap-2">
        <FileText className="size-5 shrink-0 text-muted-foreground" />
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                className="size-7"
                aria-label="Document actions"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="size-4" />
              </Button>
            }
          />
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              variant="destructive"
              onClick={(e) => {
                e.stopPropagation();
                setConfirmOpen(true);
              }}
            >
              <Trash2 className="size-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <p className="line-clamp-2 min-w-0 text-sm font-medium">{document.title}</p>

      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {document.status === "ready"
            ? `${document.page_count} pages · ${document.chunk_count} chunks`
            : " "}
        </span>
        <StatusBadge status={document.status} />
      </div>
    </Card>
  );

  return (
    <>
      {document.status === "failed" && document.error ? (
        <Tooltip>
          <TooltipTrigger render={card} />
          <TooltipContent>{document.error}</TooltipContent>
        </Tooltip>
      ) : (
        card
      )}

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this document?</DialogTitle>
            <DialogDescription>
              Deletes the document, its chats, quizzes and flashcards. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete} disabled={deleting}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
