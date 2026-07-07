import { API_BASE_URL, ApiError, NetworkError } from "@/lib/api";

export interface SseEvent {
  event: string;
  data: string;
}

/** Fetch + ReadableStream SSE parser — used instead of EventSource because
 * EventSource can't send an Authorization header. */
export async function* streamSse(
  path: string,
  token: string,
  body: unknown,
  signal?: AbortSignal
): AsyncGenerator<SseEvent> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new NetworkError();
  }

  if (!response.ok || !response.body) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const parsed = await response.json();
      if (typeof parsed?.detail === "string") detail = parsed.detail;
    } catch {
      // ignore, use generic message
    }
    throw new ApiError(response.status, detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      // sse-starlette's default line separator is "\r\n" (not "\n"), so event
      // boundaries arrive as "\r\n\r\n" — normalize before splitting, since that
      // string contains no literal "\n\n" substring for a plain split to find.
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n").replace(/\r/g, "\n");

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";

      for (const chunk of chunks) {
        let event = "message";
        const dataLines: string[] = [];
        for (const line of chunk.split("\n")) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }
        if (dataLines.length > 0) {
          yield { event, data: dataLines.join("\n") };
        }
      }
    }
  } finally {
    // Reached if the stream ends naturally, or if the caller stops iterating early
    // (e.g. breaks after "done") — releases the connection instead of leaving it
    // open for a server that never closes the response on its own.
    await reader.cancel().catch(() => {});
  }
}
