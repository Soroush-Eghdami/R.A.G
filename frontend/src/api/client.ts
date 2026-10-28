/** Every request goes through here. */

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

/** Turn DRF field errors into one readable sentence. */
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
      // Not JSON, keep the generic message.
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

/* ------------------------------------------------------------------ system */

export const getHealth = () => request<Health>("/health/");

export const getModels = (refresh = false) =>
  request<ModelsResponse>(`/models/${refresh ? "?refresh=1" : ""}`);

export const getSettings = () => request<AppSettings>("/settings/");

export const updateSettings = (patch: Partial<AppSettings>) =>
  request<AppSettings>("/settings/", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });

/* --------------------------------------------------------- knowledge bases */

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

/* ---------------------------------------------------------------- documents */

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

/* ------------------------------------------------------------ conversations */

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

/** Non-streaming answer. The streaming version lands in the chat phase. */
export const ask = (conversationId: string, question: string) =>
  request<{ message: Message; sources: Source[]; rewritten: string | null }>(
    `/conversations/${conversationId}/messages/`,
    {
      method: "POST",
      body: JSON.stringify({ question, stream: false }),
    },
  );
