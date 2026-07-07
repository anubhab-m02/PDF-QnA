import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { StreamingCursor } from "@/components/chat/streaming-cursor";
import { SourceChip } from "@/components/chat/source-chip";
import { dedupeSourcesByPage, parseSources } from "@/lib/chat";
import type { Message } from "@/lib/chat";

export function ChatBubble({
  message,
  streaming,
}: {
  message: Message;
  streaming?: boolean;
}) {
  const isUser = message.role === "user";
  const sources = dedupeSourcesByPage(parseSources(message.sources_json));

  return (
    <div className={cn("flex flex-col gap-1.5", isUser ? "items-end" : "items-start")}>
      <div
        className={cn(
          "max-w-[75%] rounded-lg px-3 py-2 text-sm",
          isUser
            ? "whitespace-pre-wrap bg-primary text-primary-foreground"
            : "border bg-card text-card-foreground"
        )}
      >
        {isUser ? (
          message.content
        ) : (
          <div className="markdown-body prose prose-sm max-w-none dark:prose-invert prose-p:my-2 prose-p:first:mt-0 prose-p:last:mb-0 prose-pre:my-2">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
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
