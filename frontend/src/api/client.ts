/** Send API requests through this helper. */

import type {
  AppSettings,
  Conversation,
  CreateKnowledgeBase,
  Document,
  Health,
  KnowledgeBase,
  Message,
  ModelsResponse,
  Source,
} from "./types";

const BASE = "/api";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** Convert field errors into one readable message. */
function describe(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object") return fallback;
  const record = body as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;

  const parts: string[] = [];
  for (const [field, value] of Object.entries(record)) {
    if (Array.isArray(value)) {
      parts.push(
        field === "non_field_errors" ? value.join(" ") : `${field}: ${value.join(" ")}`,
      );
    } else if (typeof value === "string") {
      parts.push(`${field}: ${value}`);
    }
  }
  return parts.length > 0 ? parts.join(" · ") : fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Cannot reach the backend. Is it running?", 0);
  }

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // Use the generic message for non-JSON errors.
    }
    const code =
      body && typeof body === "object"
        ? ((body as Record<string, unknown>).code as string | undefined)
        : undefined;
    throw new ApiError(
      describe(body, `Request failed (${response.status}).`),
      response.status,
      code,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// System.

export const getHealth = () => request<Health>("/health/");

export const getModels = (refresh = false) =>
  request<ModelsResponse>(`/models/${refresh ? "?refresh=1" : ""}`);

export const getSettings = () => request<AppSettings>("/settings/");

export const updateSettings = (patch: Partial<AppSettings>) =>
  request<AppSettings>("/settings/", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });

// Knowledge bases.

export const listKnowledgeBases = () => request<KnowledgeBase[]>("/knowledge-bases/");

export const getKnowledgeBase = (id: string) =>
  request<KnowledgeBase>(`/knowledge-bases/${id}/`);

export const createKnowledgeBase = (body: CreateKnowledgeBase) =>
  request<KnowledgeBase>("/knowledge-bases/", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const deleteKnowledgeBase = (id: string) =>
  request<void>(`/knowledge-bases/${id}/`, { method: "DELETE" });

// Documents.

export const listDocuments = (knowledgeBaseId: string) =>
  request<Document[]>(`/documents/?knowledge_base=${knowledgeBaseId}`);

export const uploadDocument = (knowledgeBaseId: string, file: File) => {
  const form = new FormData();
  form.append("knowledge_base", knowledgeBaseId);
  form.append("file", file);
  return request<Document>("/documents/", { method: "POST", body: form });
};

export const deleteDocument = (id: string) =>
  request<void>(`/documents/${id}/`, { method: "DELETE" });

// Conversations.

export const listConversations = (knowledgeBaseId?: string) =>
  request<Conversation[]>(
    `/conversations/${knowledgeBaseId ? `?knowledge_base=${knowledgeBaseId}` : ""}`,
  );

export const createConversation = (knowledgeBaseId: string, chatModel: string) =>
  request<Conversation>("/conversations/", {
    method: "POST",
    body: JSON.stringify({ knowledge_base: knowledgeBaseId, chat_model: chatModel }),
  });

export const getConversation = (id: string) =>
  request<Conversation>(`/conversations/${id}/`);

export const updateConversation = (id: string, patch: Record<string, unknown>) =>
  request<Conversation>(`/conversations/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });

export const deleteConversation = (id: string) =>
  request<void>(`/conversations/${id}/`, { method: "DELETE" });

/** Get a non-streaming answer. */
export const ask = (conversationId: string, question: string) =>
  request<{ message: Message; sources: Source[]; rewritten: string | null }>(
    `/conversations/${conversationId}/messages/`,
    {
      method: "POST",
      body: JSON.stringify({ question, stream: false }),
    },
  );

// Streaming.

export type StreamEvent =
  | { type: "query"; original: string; query: string }
  | { type: "sources"; sources: Source[] }
  | { type: "token"; text: string }
  | { type: "thinking"; text: string }
  | { type: "done"; messageId: number | null }
  | { type: "error"; detail: string; code: string };

/** Parse one SSE block. */
export function parseEvent(block: string): StreamEvent | null {
  let name = "";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) {
      name = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      data.push(line.slice(6));
    }
  }
  if (!name) return null;

  const raw = data.join("\n");
  if (!raw) return null;
  const payload = JSON.parse(raw) as Record<string, unknown>;

  switch (name) {
    case "query":
      return {
        type: "query",
        original: String(payload.original ?? ""),
        query: String(payload.query ?? ""),
      };
    case "sources":
      return { type: "sources", sources: payload as unknown as Source[] };
    case "token":
      return { type: "token", text: String(payload.text ?? "") };
    case "thinking":
      return { type: "thinking", text: String(payload.text ?? "") };
    case "done":
      return {
        type: "done",
        messageId: typeof payload.message_id === "number" ? payload.message_id : null,
      };
    case "error":
      return {
        type: "error",
        detail: String(payload.detail ?? "Something went wrong."),
        code: String(payload.code ?? "unknown"),
      };
    default:
      return null;
  }
}

type StreamHandlers = {
  onEvent: (event: StreamEvent) => void;
  signal?: AbortSignal;
};

/** Stream answer events to the caller. */
export async function streamAnswer(
  conversationId: string,
  question: string,
  { onEvent, signal, think = false }: StreamHandlers & { think?: boolean },
): Promise<void> {
  const response = await fetch(`${BASE}/conversations/${conversationId}/messages/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, think }),
    signal,
  });

  if (!response.ok || !response.body) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // Use the generic message.
    }
    throw new ApiError(
      describe(body, `Request failed (${response.status}).`),
      response.status,
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let split = buffer.indexOf("\n\n");
    while (split !== -1) {
      const block = buffer.slice(0, split);
      buffer = buffer.slice(split + 2);
      const event = parseEvent(block);
      if (event) onEvent(event);
      split = buffer.indexOf("\n\n");
    }
  }
}
