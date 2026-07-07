"use client";

import { useRef, type KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MAX_CHARS = 4000;
const COUNTER_THRESHOLD = 3500;
const MAX_ROWS = 6;

export function ChatInput({
  value,
  onChange,
  onSend,
  onStop,
  disabled,
  streaming,
}: {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  disabled: boolean;
  streaming: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSend();
    }
  }

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const lineHeight = 20;
    const maxHeight = lineHeight * MAX_ROWS + 16;
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  }

  return (
    <div className="flex flex-col gap-1 border-t p-4">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            onChange(e.target.value.slice(0, MAX_CHARS));
            autoResize();
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          placeholder="Ask a question about this document…"
          className="flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
        />
        {streaming ? (
          <Button type="button" variant="outline" size="icon" aria-label="Stop" onClick={onStop}>
            <Square className="size-4" />
          </Button>
        ) : (
          <Button
            type="button"
            size="icon"
            aria-label="Send"
            disabled={disabled || !value.trim()}
            onClick={onSend}
          >
            <Send className="size-4" />
          </Button>
        )}
      </div>
      {value.length > COUNTER_THRESHOLD && (
        <span
          className={cn(
            "self-end text-xs text-muted-foreground",
            value.length >= MAX_CHARS && "text-destructive"
          )}
        >
          {value.length} / {MAX_CHARS}
        </span>
      )}
    </div>
  );
}
