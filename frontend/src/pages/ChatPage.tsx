import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ApiError,
  createConversation,
  deleteConversation,
  getConversation,
  getSettings,
  listConversations,
  listKnowledgeBases,
  streamAnswer,
  updateConversation,
} from "../api/client";
import type { Message, Source } from "../api/types";
import { useModels } from "../lib/hooks";
import { cx, formatDate } from "../lib/format";
import AnswerMarkdown from "../components/AnswerMarkdown";
import SourceDrawer from "../components/SourceDrawer";
import {
  ChatIcon,
  CloseIcon,
  FileIcon,
  PlusIcon,
  SendIcon,
  SparkIcon,
  StopIcon,
} from "../components/icons";
import { Badge, Banner, Button, EmptyState, Spinner } from "../components/ui";

function ThinkingBlock({ thinking }: { thinking: string }) {
  return (
    <details className="group border border-line/50 rounded-xl bg-app/50 overflow-hidden">
      <summary className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-muted cursor-pointer list-none transition hover:text-ink">
        <span className="grid size-5 place-items-center rounded-lg bg-primary/10 text-primary ring-1 ring-inset ring-primary/20">
          <SparkIcon className="size-3" />
        </span>
        <span>Thinking</span>
        <span className="ml-auto size-4 text-muted transition group-open:rotate-180">
          <SparkIcon className="size-3" />
        </span>
      </summary>
      <div className="px-4 pb-3 pt-0 text-xs font-mono text-muted/80 leading-relaxed whitespace-pre-wrap">
        {thinking}
      </div>
    </details>
  );
}

type Draft = { text: string; sources: Source[]; rewritten: string | null; thinking: string };

const KB_KEY = "rag.kb";
const MODEL_KEY = "rag.model";

function remember(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Browser storage may be unavailable.
  }
}

function recall(key: string): string {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

export default function ChatPage() {
  const { id: conversationId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const kbs = useQuery({ queryKey: ["kbs"], queryFn: listKnowledgeBases });
  const models = useModels();
  const settings = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [kbId, setKbId] = useState(() => recall(KB_KEY));
  const [model, setModel] = useState(() => recall(MODEL_KEY));
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [stream, setStream] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stopped, setStopped] = useState(false);
  const [citations, setCitations] = useState<{ sources: Source[]; active: number } | null>(
    null,
  );
  const [think, setThink] = useState(() => recall("rag.think") === "true");

  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const conversations = useQuery({
    queryKey: ["conversations", kbId],
    queryFn: () => listConversations(kbId),
    enabled: Boolean(kbId),
  });

  const conversation = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => getConversation(conversationId!),
    enabled: Boolean(conversationId),
  });

  // Use the linked knowledge base, or choose the first one.
  useEffect(() => {
    if (!kbs.data || kbs.data.length === 0) return;
    if (conversation.data?.knowledge_base) {
      if (conversation.data.knowledge_base !== kbId) {
        setKbId(conversation.data.knowledge_base);
      }
      return;
    }
    if (kbId && kbs.data.some((kb) => kb.id === kbId)) return;
    setKbId(kbs.data[0].id);
  }, [kbs.data, conversation.data, kbId]);

  useEffect(() => {
    if (kbId) remember(KB_KEY, kbId);
  }, [kbId]);

  // Use the configured model, or the first available one.
  useEffect(() => {
    if (model || !models.data) return;
    const preferred = settings.data?.default_chat_model ?? "";
    const installed = models.data.chat.some((item) => item.name === preferred);
    setModel(installed ? preferred : (models.data.chat[0]?.name ?? ""));
  }, [model, models.data, settings.data]);

  useEffect(() => {
    if (model) remember(MODEL_KEY, model);
  }, [model]);

  // Load the conversation from the URL.
  useEffect(() => {
    if (conversationId) {
      if (conversation.data?.id === conversationId) {
        setMessages(conversation.data.messages);
      }
      if (conversation.data?.chat_model) setModel(conversation.data.chat_model);
    } else {
      setMessages([]);
    }
  }, [conversationId, conversation.data]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages, stream?.text]);

  const switchModel = useMutation({
    mutationFn: (next: string) => updateConversation(conversationId!, { chat_model: next }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", conversationId] });
    },
  });

  const removeConversation = useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", kbId] });
      navigate("/chat");
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.message : "Could not delete that chat."),
  });

  function changeModel(next: string) {
    setModel(next);
    if (conversationId) switchModel.mutate(next);
  }

  async function send() {
    const question = draft.trim();
    if (!question || stream) return;
    if (!kbId) {
      setError("Create a knowledge base first.");
      return;
    }
    if (!model) {
      setError("Pick a chat model first.");
      return;
    }

    setDraft("");
    setError(null);
    setStopped(false);

    let id = conversationId;
    try {
      if (!id) {
        const created = await createConversation(kbId, model);
        id = created.id;
        navigate(`/chat/${id}`, { replace: true });
        queryClient.invalidateQueries({ queryKey: ["conversations", kbId] });
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start a chat.");
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: -Date.now(),
        role: "user",
        content: question,
        sources: [],
        model_used: "",
        created_at: new Date().toISOString(),
      },
    ]);
    setStream({ text: "", sources: [], rewritten: null, thinking: "" });

    const controller = new AbortController();
    abortRef.current = controller;

    let text = "";
    let thinking = "";
    let sources: Source[] = [];
    let rewritten: string | null = null;
    let failed: string | null = null;

    try {
      await streamAnswer(id, question, {
        signal: controller.signal,
        think,
        onEvent: (event) => {
          if (event.type === "query") {
            rewritten = event.query;
            setStream((current) => (current ? { ...current, rewritten } : current));
          } else if (event.type === "sources") {
            sources = event.sources;
            setStream((current) => (current ? { ...current, sources } : current));
          } else if (event.type === "token") {
            text += event.text;
            setStream((current) => (current ? { ...current, text } : current));
          } else if (event.type === "thinking") {
            thinking += event.text;
            setStream((current) => (current ? { ...current, thinking } : current));
          } else if (event.type === "error") {
            failed = event.detail;
          }
        },
      });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setStopped(true);
      } else if (err instanceof ApiError) {
        failed = err.message;
      } else {
        failed = "The connection dropped while answering.";
      }
    } finally {
      abortRef.current = null;
    }

    if (text || sources.length > 0) {
      setMessages((current) => [
        ...current,
        {
          id: -Date.now() - 1,
          role: "assistant",
          content: text,
          sources,
          model_used: model,
          created_at: new Date().toISOString(),
        },
      ]);
    }
    setStream(null);
    if (failed) setError(failed);

    queryClient.invalidateQueries({ queryKey: ["conversation", id] });
    queryClient.invalidateQueries({ queryKey: ["conversations", kbId] });
  }

  const activeConversation = conversation.data;
  const noKbs = kbs.isSuccess && kbs.data.length === 0;
  const kbName = kbs.data?.find((kb) => kb.id === kbId)?.name ?? "";
  const count = activeConversation?.message_count ?? 0;

  const kbPicker = (className?: string) => (
    <select
      className={cx(
        "w-full cursor-pointer rounded-lg border border-line bg-elevated px-2.5 py-2 text-xs font-medium text-ink outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20",
        className,
      )}
      value={kbId}
      onChange={(event) => {
        setKbId(event.target.value);
        navigate("/chat");
      }}
      aria-label="Knowledge base"
    >
      {(kbs.data ?? []).map((kb) => (
        <option key={kb.id} value={kb.id}>
          {kb.name}
        </option>
      ))}
    </select>
  );

  return (
    <div className="flex h-[calc(100dvh-7.5rem)] min-h-[28rem] overflow-hidden rounded-3xl border border-line bg-surface/90 shadow-[0_20px_60px_-35px_rgb(0_0_0_/_0.5)] backdrop-blur-sm md:h-[calc(100dvh-7rem)]">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-line bg-app/50 lg:flex">
        <div className="space-y-2 p-3">
          <p className="px-1 text-[11px] font-medium tracking-wide text-muted uppercase">
            Knowledge base
          </p>
          {kbPicker()}
          <Button variant="primary" className="w-full" onClick={() => navigate("/chat")}>
            <PlusIcon />
            New chat
          </Button>
        </div>

        <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
          <p className="px-2 pt-1 pb-1 text-[11px] font-medium tracking-wide text-muted uppercase">
            Chats
          </p>

          {conversations.data?.length === 0 ? (
            <p className="px-2 py-2 text-xs text-muted">No chats yet.</p>
          ) : null}

          {conversations.data?.map((item) => {
            const isActive = item.id === conversationId;
            return (
              <div
                key={item.id}
                className={cx(
                  "group flex items-center gap-1 rounded-lg pr-1 transition",
                  isActive ? "bg-elevated" : "hover:bg-elevated/60",
                )}
              >
                <button
                  type="button"
                  className="min-w-0 flex-1 cursor-pointer rounded-lg px-2.5 py-2 text-left"
                  onClick={() => navigate(`/chat/${item.id}`)}
                >
                  <span
                    className={cx(
                      "block truncate text-xs font-medium",
                      isActive ? "text-ink" : "text-ink/80",
                    )}
                  >
                    {item.title || "New chat"}
                  </span>
                  <span className="block text-[11px] text-muted">
                    {formatDate(item.updated_at)}
                  </span>
                </button>
                <button
                  type="button"
                  aria-label="Delete chat"
                  className="cursor-pointer rounded-md p-1 text-muted opacity-0 transition group-hover:opacity-100 hover:bg-danger/10 hover:text-danger"
                  onClick={() => {
                    if (window.confirm("Delete this chat?")) removeConversation.mutate(item.id);
                  }}
                >
                  <CloseIcon className="size-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="hidden size-9 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary sm:grid">
              <ChatIcon className="size-[18px]" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">
                {activeConversation?.title || "New chat"}
              </p>
              <p className="truncate text-xs text-muted">
                {activeConversation
                  ? `${count} message${count === 1 ? "" : "s"}${kbName ? ` · ${kbName}` : ""}`
                  : kbName || "Ask something about the selected knowledge base"}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <div className="lg:hidden">{kbPicker("max-w-40")}</div>
            <label className="flex items-center gap-1.5 cursor-pointer text-xs text-muted hover:text-ink" title="Enable reasoning mode">
              <input
                type="checkbox"
                checked={think}
                onChange={(event) => {
                  setThink(event.target.checked);
                  localStorage.setItem("rag.think", String(event.target.checked));
                }}
                className="size-4 accent-primary"
              />
              <SparkIcon className="size-3.5" />
              <span>Think</span>
            </label>
            <select
              className="max-w-56 cursor-pointer rounded-lg border border-line bg-elevated px-2.5 py-2 text-xs font-medium text-ink outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
              value={model}
              onChange={(event) => changeModel(event.target.value)}
              aria-label="Chat model"
            >
              {!model ? (
                <option value="">
                  {models.data ? "Pick a model" : "Loading models…"}
                </option>
              ) : null}
              {models.data && !models.data.chat.some((item) => item.name === model) && model ? (
                <option value={model}>{model} (not installed)</option>
              ) : null}
              {(models.data?.chat ?? []).map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-5">
          <div className="mx-auto w-full max-w-3xl space-y-6">
            {error ? <Banner>{error}</Banner> : null}

            {noKbs ? (
              <EmptyState
                icon={<FileIcon className="size-5" />}
                title="No knowledge base yet"
                hint="Create one and upload a document before asking questions."
                action={
                  <Link
                    to="/kb"
                    className="inline-flex items-center gap-2 rounded-xl bg-primary px-3.5 py-2 text-sm font-medium text-on-primary shadow-sm shadow-primary/25 transition hover:bg-primary-hover"
                  >
                    Go to knowledge bases
                  </Link>
                }
              />
            ) : null}

            {!noKbs && messages.length === 0 && !stream ? (
              <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
                <span className="grid size-12 place-items-center rounded-2xl bg-accent/10 text-accent ring-1 ring-inset ring-accent/20">
                  <SparkIcon className="size-6" />
                </span>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-ink">
                    Ask anything about your documents
                  </p>
                  <p className="mx-auto max-w-sm text-xs text-muted">
                    Answers cite the passages they used. Click a citation to read the
                    source.
                  </p>
                </div>
              </div>
            ) : null}

            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onCite={(n) => setCitations({ sources: message.sources, active: n })}
              />
            ))}

            {stream ? (
              <div className="animate-rise space-y-2">
                {stream.rewritten ? (
                  <p className="text-[11px] text-muted">
                    searched for <span className="text-accent">{stream.rewritten}</span>
                  </p>
                ) : null}

                {stream.thinking ? (
                  <ThinkingBlock thinking={stream.thinking} />
                ) : null}

                {stream.text ? (
                  <AnswerMarkdown
                    text={stream.text}
                    onCite={(n) => setCitations({ sources: stream.sources, active: n })}
                  />
                ) : (
                  <div className="flex items-center gap-2 text-xs text-muted">
                    <Spinner /> Thinking…
                  </div>
                )}

                {stopped ? (
                  <Badge tone="warn">stopped</Badge>
                ) : (
                  <span className="inline-block h-4 w-[3px] animate-pulse rounded-full bg-accent align-middle" />
                )}
              </div>
            ) : null}

            <div ref={bottomRef} />
          </div>
        </div>

        <footer className="border-t border-line px-5 py-3.5">
          <div className="mx-auto w-full max-w-3xl">
            <div className="flex items-end gap-2 rounded-2xl border border-line bg-elevated p-1.5 transition focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/15">
              <textarea
                className="max-h-40 min-h-10 w-full resize-none bg-transparent px-2.5 py-2 text-sm text-ink outline-none placeholder:text-muted/70 disabled:opacity-60"
                placeholder="Ask a question…"
                rows={1}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void send();
                  }
                }}
                disabled={Boolean(stream) || noKbs}
              />

              {stream ? (
                <Button
                  variant="danger"
                  className="shrink-0"
                  onClick={() => abortRef.current?.abort()}
                >
                  <StopIcon />
                  Stop
                </Button>
              ) : (
                <Button
                  variant="primary"
                  className="shrink-0 px-3.5"
                  onClick={() => void send()}
                  disabled={!draft.trim() || !model || noKbs}
                  title={!model ? "Waiting for the model list" : undefined}
                  aria-label="Send"
                >
                  <SendIcon className="size-[18px]" />
                </Button>
              )}
            </div>
            <p className="mt-2 text-center text-[11px] text-muted">
              Enter to send · Shift+Enter for a new line
            </p>
          </div>
        </footer>
      </section>

      {citations ? (
        <SourceDrawer
          sources={citations.sources}
          active={citations.active}
          onSelect={(n) => setCitations({ ...citations, active: n })}
          onClose={() => setCitations(null)}
        />
      ) : null}
    </div>
  );
}

function MessageBubble({
  message,
  onCite,
}: {
  message: Message;
  onCite: (n: number) => void;
}) {
  if (message.role === "user") {
    return (
      <div className="animate-rise flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md border border-line bg-elevated px-4 py-2.5 text-sm text-ink shadow-sm">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-rise space-y-2.5">
      <AnswerMarkdown text={message.content} onCite={onCite} />

      {message.sources.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {message.sources.map((source) => (
            <button
              key={source.n}
              type="button"
              onClick={() => onCite(source.n)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-accent/20 bg-accent/5 px-2 py-1 text-[11px] font-medium text-accent transition hover:border-accent/40 hover:bg-accent/10"
            >
              <span className="font-semibold">[{source.n}]</span>
              <span className="max-w-40 truncate">
                {source.document || "source"}
                {source.page !== null ? `, p.${source.page}` : ""}
              </span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
