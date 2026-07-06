import { cn } from "@/lib/utils";
import type { Document } from "@/lib/documents";

const STYLES: Record<Document["status"], string> = {
  processing: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  ready: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  failed: "bg-red-500/15 text-red-600 dark:text-red-400",
};

const LABELS: Record<Document["status"], string> = {
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: Document["status"] }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium",
        STYLES[status]
      )}
      aria-busy={status === "processing"}
    >
      <span
        className={cn(
          "size-1.5 rounded-full bg-current",
          status === "processing" && "animate-pulse"
        )}
      />
      {LABELS[status]}
    </span>
  );
}
