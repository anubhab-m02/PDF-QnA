import { cn } from "@/lib/utils";
import { StreamingCursor } from "@/components/chat/streaming-cursor";
import { SourceChip } from "@/components/chat/source-chip";
import { parseSources } from "@/lib/chat";
import type { Message } from "@/lib/chat";

export function ChatBubble({
  message,
  streaming,
}: {
  message: Message;
  streaming?: boolean;
}) {
  const isUser = message.role === "user";
  const sources = parseSources(message.sources_json);

  return (
    <div className={cn("flex flex-col gap-1.5", isUser ? "items-end" : "items-start")}>
      <div
        className={cn(
          "max-w-[75%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm",
          isUser
            ? "bg-primary text-primary-foreground"
            : "border bg-card text-card-foreground"
        )}
      >
        {message.content}
        {streaming && <StreamingCursor />}
      </div>
      {!isUser && sources.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pl-1">
          {sources.map((source, i) => (
            <SourceChip key={i} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}
