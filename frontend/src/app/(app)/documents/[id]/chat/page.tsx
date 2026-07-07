"use client";

import { use, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";
import { ChatBubble } from "@/components/chat/chat-bubble";
import { ChatInput } from "@/components/chat/chat-input";
import { SessionSwitcher } from "@/components/chat/session-switcher";
import { DocumentNav } from "@/components/documents/document-nav";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { apiFetch, authHeaders, ApiError, NetworkError } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import { useAuth } from "@/lib/auth";
import type { ChatSession, Message } from "@/lib/chat";
import type { Document } from "@/lib/documents";

const SUGGESTED_QUESTIONS = [
  "Summarize the key ideas",
  "What are the main takeaways?",
  "Explain this in simpler terms",
];

export default function DocumentChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const documentId = Number(id);
  const { token } = useAuth();

  const [document, setDocument] = useState<Document | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastSentRef = useRef<string>("");
  const userStoppedRef = useRef(false);

  useEffect(() => {
    if (!token || Number.isNaN(documentId)) return;

    (async () => {
      try {
        const [doc, allSessions] = await Promise.all([
          apiFetch<Document>(`/api/documents/${documentId}`, { headers: authHeaders(token) }),
          apiFetch<ChatSession[]>("/api/chat/sessions", { headers: authHeaders(token) }),
        ]);
        setDocument(doc);
        const docSessions = allSessions.filter((s) => s.document_id === documentId);
        setSessions(docSessions);

        if (docSessions.length > 0) {
          setActiveSessionId(docSessions[0].id);
        } else {
          const created = await apiFetch<ChatSession>("/api/chat/sessions", {
            method: "POST",
            headers: authHeaders(token),
            body: JSON.stringify({ document_id: documentId, title: "New chat" }),
          });
          setSessions([created]);
          setActiveSessionId(created.id);
        }
      } catch (err) {
        if (err instanceof ApiError || err instanceof NetworkError) toast.error(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [token, documentId]);

  useEffect(() => {
    if (!token || activeSessionId === null) return;
    (async () => {
      try {
        const msgs = await apiFetch<Message[]>(
          `/api/chat/sessions/${activeSessionId}/messages`,
          { headers: authHeaders(token) }
        );
        setMessages(msgs);
      } catch (err) {
        if (err instanceof ApiError || err instanceof NetworkError) toast.error(err.message);
      }
    })();
  }, [token, activeSessionId]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (atBottom) el.scrollTop = el.scrollHeight;
  }, [messages, streamingText]);

  // A stream that goes quiet for this long (no token/done event) is treated as dead —
  // guards against a connection that never signals completion (seen in practice with
  // some SSE server configurations that keep the socket open after the generator ends).
  const STREAM_IDLE_TIMEOUT_MS = 45_000;

  function resetStreamingState() {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreamingText(null);
    setStreamError(null);
  }

  async function handleCreateSession() {
    if (!token) return;
    resetStreamingState();
    const created = await apiFetch<ChatSession>("/api/chat/sessions", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ document_id: documentId, title: "New chat" }),
    });
    setSessions((prev) => [created, ...prev]);
    setActiveSessionId(created.id);
    setMessages([]);
  }

  function handleSelectSession(sessionId: number) {
    resetStreamingState();
    setActiveSessionId(sessionId);
  }

  async function sendMessage(content: string) {
    if (!token || activeSessionId === null || !content.trim()) return;

    lastSentRef.current = content;
    userStoppedRef.current = false;
    setStreamError(null);
    setInput("");
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role: "user",
        content,
        sources_json: null,
        created_at: new Date().toISOString(),
      },
    ]);
    setStreamingText("");

    const controller = new AbortController();
    abortRef.current = controller;

    let idleTimer: ReturnType<typeof setTimeout> | undefined;
    const resetIdleTimer = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => controller.abort(), STREAM_IDLE_TIMEOUT_MS);
    };
    resetIdleTimer();

    let fullText = "";
    let finishedCleanly = false;
    let errorMessage: string | null = null;

    try {
      for await (const evt of streamSse(
        `/api/chat/sessions/${activeSessionId}/messages`,
        token,
        { content },
        controller.signal
      )) {
        resetIdleTimer();

        if (evt.event === "token") {
          fullText += evt.data;
          setStreamingText(fullText);
        } else if (evt.event === "done") {
          finishedCleanly = true;
          // Stop consuming as soon as "done" arrives — some SSE server configurations
          // keep the underlying connection open indefinitely afterward, and waiting
          // for the `for await` loop to end naturally would hang here forever.
          break;
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // Either the user clicked Stop (silent, expected) or the idle timeout fired
        // (surface as an interruption so the user knows to retry).
        if (!userStoppedRef.current) errorMessage = "Response interrupted";
      } else {
        errorMessage =
          err instanceof ApiError || err instanceof NetworkError
            ? err.message
            : "Response interrupted";
      }
    } finally {
      clearTimeout(idleTimer);
      abortRef.current = null;
    }

    // Regardless of how the stream ended — done event, abort, idle timeout, or any
    // other error — always leave the UI in a terminal (non-streaming) state and
    // persist whatever text actually arrived, so it's never silently lost.
    setStreamingText(null);
    if (fullText) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: "assistant",
          content: fullText,
          sources_json: null,
          created_at: new Date().toISOString(),
        },
      ]);
    }
    if (errorMessage) setStreamError(errorMessage);

    // The authoritative copy (with sources) is persisted server-side by the time the
    // "done" event fires — refetch to replace our sourceless optimistic bubble with it.
    if (finishedCleanly) {
      try {
        const msgs = await apiFetch<Message[]>(
          `/api/chat/sessions/${activeSessionId}/messages`,
          { headers: authHeaders(token) }
        );
        setMessages(msgs);
      } catch {
        // Keep the optimistic messages if the refetch fails — not fatal.
      }
    }
  }

  function handleStop() {
    userStoppedRef.current = true;
    abortRef.current?.abort();
  }

  function handleRetry() {
    // Only drop a trailing partial assistant reply — never the user's own message,
    // which is still there even if the stream failed before any tokens arrived.
    setMessages((prev) =>
      prev.length > 0 && prev[prev.length - 1].role === "assistant" ? prev.slice(0, -1) : prev
    );
    sendMessage(lastSentRef.current);
  }

  const streaming = streamingText !== null;

  return (
    <div className="flex h-full flex-col">
      <DocumentNav documentId={documentId} />
      <div className="flex items-center justify-between border-b px-4 py-3">
        <p className="min-w-0 truncate font-medium">{document?.title ?? "Chat"}</p>
        <SessionSwitcher
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={handleSelectSession}
          onCreate={handleCreateSession}
        />
      </div>

      <div ref={scrollRef} aria-live="polite" className="flex-1 space-y-4 overflow-y-auto p-4">
        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-10 w-2/3" />
            <Skeleton className="ml-auto h-10 w-1/2" />
          </div>
        )}

        {!loading && messages.length === 0 && !streaming && (
          <div className="flex flex-wrap gap-2 pt-8">
            {SUGGESTED_QUESTIONS.map((q) => (
              <Button key={q} variant="outline" size="sm" onClick={() => sendMessage(q)}>
                {q}
              </Button>
            ))}
          </div>
        )}

        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}

        {streaming && (
          <ChatBubble
            message={{
              id: -1,
              role: "assistant",
              content: streamingText ?? "",
              sources_json: null,
              created_at: new Date().toISOString(),
            }}
            streaming
          />
        )}

        {streamError && (
          <div className="flex items-center gap-2 text-xs text-destructive">
            <AlertCircle className="size-3.5" />
            {streamError} —{" "}
            <button type="button" onClick={handleRetry} className="underline">
              Retry
            </button>
          </div>
        )}
      </div>

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={() => sendMessage(input)}
        onStop={handleStop}
        disabled={streaming || activeSessionId === null}
        streaming={streaming}
      />
    </div>
  );
}
