/** API response types. */

export type ModelKind = "chat" | "embedding";

export type ModelInfo = {
  name: string;
  kind: ModelKind;
  capabilities: string[];
  size_bytes: number;
  parameter_size: string;
  quantization: string;
  family: string;
  context_length: number | null;
  is_cloud: boolean;
};

export type ModelsResponse = {
  chat: ModelInfo[];
  embedding: ModelInfo[];
  chat_base_url: string;
  embedding_base_url: string;
};

export type Health = {
  status: "ok" | "degraded";
  chat: {
    reachable: boolean;
    base_url: string;
    error: string | null;
  };
  embedding: {
    reachable: boolean;
    base_url: string;
    error: string | null;
  };
  database: { ok: boolean };
};

export type KnowledgeBase = {
  id: string;
  name: string;
  description: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  is_locked: boolean;
  document_count: number;
  created_at: string;
};

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export type Document = {
  id: string;
  knowledge_base: string;
  original_name: string;
  file_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error: string;
  page_count: number | null;
  chunk_count: number;
  file_url: string | null;
  created_at: string;
  updated_at: string;
};

export type AppSettings = {
  default_chat_model: string;
  default_embedding_model: string;
  top_k: number;
  temperature: number;
  num_ctx: number;
  llama_cpp_chat_base_url: string;
  llama_cpp_embedding_base_url: string;
  max_num_ctx: number;
  updated_at: string;
};

export type Source = {
  n: number;
  document_id: string;
  document: string;
  page: number | null;
  distance: number;
  snippet: string;
};

export type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources: Source[];
  model_used: string;
  created_at: string;
};

export type Conversation = {
  id: string;
  knowledge_base: string;
  title: string;
  chat_model: string;
  message_count: number;
  messages: Message[];
  created_at: string;
  updated_at: string;
};

export type CreateKnowledgeBase = {
  name: string;
  description?: string;
  embedding_model: string;
};
