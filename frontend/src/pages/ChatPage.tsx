import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
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
import type { AnswerLength, KnowledgeBase, Message, Source } from "../api/types";
import { useModels } from "../lib/hooks";
import { cx, formatDate } from "../lib/format";
import AnswerMarkdown from "../components/AnswerMarkdown";
import SourceDrawer from "../components/SourceDrawer";
import {
  ChatIcon,
  ArrowDownIcon,
  ChevronDownIcon,
  CloseIcon,
  DatabaseIcon,
  FileIcon,
  BrainIcon,
  LibraryIcon,
  PanelIcon,
  PlusIcon,
  SendIcon,
  StopIcon,
} from "../components/icons";
import { Badge, Banner, Button, Spinner } from "../components/ui";

function KnowledgeBasePicker({
  knowledgeBases,
  selectedId,
  onSelect,
  className,
}: {
  knowledgeBases: KnowledgeBase[];
  selectedId: string;
  onSelect: (id: string) => void;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();
  const selectedIndex = Math.max(
    0,
    knowledgeBases.findIndex((knowledgeBase) => knowledgeBase.id === selectedId),
  );

  useEffect(() => {
    if (!open) return;

    function closeOnOutsideClick(event: PointerEvent) {
      if (event.target instanceof Node && !rootRef.current?.contains(event.target)) {
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", closeOnOutsideClick);
    return () => document.removeEventListener("pointerdown", closeOnOutsideClick);
  }, [open]);

  function focusOption(index: number) {
    const options = rootRef.current?.querySelectorAll<HTMLButtonElement>('[role="option"]');
    options?.[index]?.focus();
  }

  function openAt(index: number) {
    setOpen(true);
    requestAnimationFrame(() => focusOption(index));
  }

  function handleToggleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      openAt(selectedIndex);
    } else if (event.key === "Escape" && open) {
      event.preventDefault();
      setOpen(false);
    }
  }

  function handleMenuKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (!knowledgeBases.length) return;
    const activeIndex = knowledgeBases.findIndex(
      (knowledgeBase) => knowledgeBase.id === document.activeElement?.getAttribute("data-kb-id"),
    );
    const currentIndex = activeIndex < 0 ? selectedIndex : activeIndex;

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      focusOption((currentIndex + direction + knowledgeBases.length) % knowledgeBases.length);
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      focusOption(event.key === "Home" ? 0 : knowledgeBases.length - 1);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
      toggleRef.current?.focus();
    }
  }

  return (
    <div ref={rootRef} className={cx("relative w-full min-w-0", className)}>
      <button
        ref={toggleRef}
        type="button"
        className="flex w-full min-w-0 cursor-pointer items-center gap-2.5 rounded-xl border border-line bg-surface px-3 py-2.5 text-left text-xs font-medium text-ink transition hover:border-primary/40 hover:bg-elevated focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
        aria-label="Knowledge base"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((isOpen) => !isOpen)}
        onKeyDown={handleToggleKeyDown}
      >
        <LibraryIcon className="size-4 shrink-0 text-primary" />
        <span className="min-w-0 flex-1 truncate">
          {knowledgeBases.find((knowledgeBase) => knowledgeBase.id === selectedId)?.name ??
            "Choose a knowledge base"}
        </span>
        <ChevronDownIcon
          className={cx("size-4 shrink-0 text-muted transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div
          id={menuId}
          role="listbox"
          aria-label="Knowledge bases"
          className="absolute left-0 top-[calc(100%+8px)] z-50 max-h-64 w-full min-w-max overflow-y-auto rounded-2xl border border-line bg-surface p-1.5 shadow-xl shadow-app/40 animate-rise"
          onKeyDown={handleMenuKeyDown}
        >
          {knowledgeBases.map((knowledgeBase) => {
            const selected = knowledgeBase.id === selectedId;
            return (
              <button
                key={knowledgeBase.id}
                type="button"
                role="option"
                aria-selected={selected}
                data-kb-id={knowledgeBase.id}
                className={cx(
                  "flex w-full cursor-pointer items-center rounded-xl px-3 py-2.5 text-left text-xs transition",
                  selected
                    ? "bg-primary-soft font-semibold text-primary"
                    : "text-ink-soft hover:bg-elevated hover:text-ink",
                )}
                onClick={() => {
                  onSelect(knowledgeBase.id);
                  setOpen(false);
                  toggleRef.current?.focus();
                }}
              >
                <span className="truncate">{knowledgeBase.name}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ThinkingBlock({ thinking }: { thinking: string }) {
  return (
    <details className="group border border-line/50 rounded-xl bg-app/50 overflow-hidden">
      <summary className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-muted cursor-pointer list-none transition hover:text-ink">
        <span className="grid size-5 place-items-center rounded-lg bg-primary/10 text-primary ring-1 ring-inset ring-primary/20">
          <BrainIcon className="size-3.5" />
        </span>
        <span>Thinking</span>
        <ChevronDownIcon className="ml-auto size-4 text-muted transition-transform group-open:rotate-180" />
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
const ANSWER_LENGTH_KEY = "rag.answerLength";

function answerLengthValue(value: string): AnswerLength {
  return value === "short" || value === "balanced" ? value : "detailed";
}

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

function thinkingLogsKey(conversationId: string) {
  return `rag.thinking.${conversationId}`;
}

function readThinkingLogs(conversationId: string): Record<string, string> {
  try {
    const stored: unknown = JSON.parse(
      localStorage.getItem(thinkingLogsKey(conversationId)) ?? "{}",
    );
    if (!stored || typeof stored !== "object" || Array.isArray(stored)) return {};
    return Object.fromEntries(
      Object.entries(stored).filter((entry): entry is [string, string] => typeof entry[1] === "string"),
    );
  } catch {
    return {};
  }
}

function saveThinkingLog(conversationId: string, assistantIndex: number, thinking: string) {
  try {
    const logs = readThinkingLogs(conversationId);
    logs[String(assistantIndex)] = thinking;
    localStorage.setItem(thinkingLogsKey(conversationId), JSON.stringify(logs));
  } catch {
    // Keep the log in the current conversation if browser storage is unavailable.
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
  const [libraryOpen, setLibraryOpen] = useState(
    () => typeof window !== "undefined" && window.innerWidth >= 1024,
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [stream, setStream] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stopped, setStopped] = useState(false);
  const [citations, setCitations] = useState<{ sources: Source[]; active: number } | null>(
    null,
  );
  const [think, setThink] = useState(() => recall("rag.think") === "true");
  const [answerLength, setAnswerLength] = useState<AnswerLength>(() =>
    answerLengthValue(recall(ANSWER_LENGTH_KEY)),
  );
  const [isAtBottom, setIsAtBottom] = useState(true);

  const abortRef = useRef<AbortController | null>(null);
  const messageListRef = useRef<HTMLDivElement>(null);
  const autoFollowRef = useRef(true);

  useEffect(() => {
    const breakpoint = window.matchMedia("(min-width: 1024px)");
    const updatePanel = () => setLibraryOpen(breakpoint.matches);
    breakpoint.addEventListener("change", updatePanel);
    return () => breakpoint.removeEventListener("change", updatePanel);
  }, []);

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
        const logs = readThinkingLogs(conversationId);
        let assistantIndex = 0;
        setMessages(
          conversation.data.messages.map((message) => {
            if (message.role !== "assistant") return message;
            const thinking = logs[String(assistantIndex)];
            assistantIndex += 1;
            return thinking ? { ...message, thinking } : message;
          }),
        );
      }
      if (conversation.data?.chat_model) setModel(conversation.data.chat_model);
    } else {
      setMessages([]);
    }
  }, [conversationId, conversation.data]);

  useEffect(() => {
    autoFollowRef.current = true;
    setIsAtBottom(true);
  }, [conversationId]);

  useEffect(() => {
    const list = messageListRef.current;
    if (!list || !autoFollowRef.current || (!messages.length && !stream?.text && !stream?.thinking)) return;
    list.scrollTop = list.scrollHeight;
  }, [messages, stream, conversationId]);

  function handleMessageScroll() {
    const list = messageListRef.current;
    if (!list) return;
    const atBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 48;
    autoFollowRef.current = atBottom;
    setIsAtBottom((current) => (current === atBottom ? current : atBottom));
  }

  function scrollToLatest() {
    const list = messageListRef.current;
    if (!list) return;
    autoFollowRef.current = true;
    setIsAtBottom(true);
    list.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
  }

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
    autoFollowRef.current = true;
    setIsAtBottom(true);

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
        answerLength,
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

    const assistantIndex = messages.filter((message) => message.role === "assistant").length;
    if (thinking) saveThinkingLog(id, assistantIndex, thinking);
    if (text || sources.length > 0 || thinking) {
      setMessages((current) => [
        ...current,
        {
          id: -Date.now() - 1,
          role: "assistant",
          content: text,
          thinking,
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
  const selectedKb = kbs.data?.find((kb) => kb.id === kbId);
  const kbName = selectedKb?.name ?? "";
  const count = activeConversation?.message_count ?? 0;

  const selectKnowledgeBase = (id: string) => {
    setKbId(id);
    navigate("/chat");
  };

  return (
    <div className="chat-workspace relative mx-auto flex h-[calc(100dvh-148px)] min-h-[360px] w-full overflow-hidden border-y border-line md:h-[calc(100dvh-32px)] md:min-h-[420px] md:rounded-2xl md:border md:shadow-[0_16px_50px_-36px_rgb(35_55_90_/_0.22)]">
      {libraryOpen ? (
        <button
          type="button"
          aria-label="Close conversation panel"
          className="panel-backdrop absolute inset-y-0 right-0 z-10 lg:hidden"
          onClick={() => setLibraryOpen(false)}
        />
      ) : null}
      <aside
        className={cx(
          "w-[242px] shrink-0 flex-col border-r border-line bg-sidebar",
          libraryOpen
            ? "absolute inset-y-0 left-0 z-20 flex w-[min(82vw,300px)] shadow-xl lg:static lg:z-auto lg:w-[242px] lg:shadow-none"
            : "hidden",
        )}
      >
        <div className="space-y-4 border-b border-line p-4">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-semibold tracking-[0.12em] text-muted uppercase">
              Your library
            </p>
            <div className="flex items-center gap-1">
              <Link
                to="/kb"
                className="rounded-lg p-1.5 text-muted transition hover:bg-elevated hover:text-ink"
                aria-label="Manage knowledge bases"
                title="Manage knowledge bases"
              >
                <FileIcon className="size-4" />
              </Link>
              <Button
                variant="ghost"
                className="size-8 px-0 lg:hidden"
                aria-label="Close conversation panel"
                onClick={() => setLibraryOpen(false)}
              >
                <CloseIcon className="size-4" />
              </Button>
            </div>
          </div>
          <KnowledgeBasePicker
            knowledgeBases={kbs.data ?? []}
            selectedId={kbId}
            onSelect={selectKnowledgeBase}
          />
          <Button
            variant="primary"
            className="w-full justify-start rounded-xl"
            onClick={() => navigate("/chat")}
          >
            <PlusIcon />
            New conversation
          </Button>
        </div>

        <div className="flex-1 space-y-1 overflow-y-auto p-3">
          <p className="px-2 pb-1 pt-1 text-[10px] font-semibold tracking-[0.12em] text-muted uppercase">
            Recent conversations
          </p>
          {conversations.data?.length === 0 ? (
            <p className="px-2 py-3 text-xs leading-relaxed text-muted">
              Your conversations will appear here.
            </p>
          ) : null}
          {conversations.data?.map((item) => {
            const isActive = item.id === conversationId;
            return (
              <div
                key={item.id}
                className={cx(
                  "group flex items-center gap-1 rounded-xl transition-colors",
                  isActive ? "bg-elevated" : "hover:bg-elevated/70",
                )}
              >
                <button
                  type="button"
                  className="min-w-0 flex-1 cursor-pointer rounded-xl px-2.5 py-2 text-left"
                  onClick={() => navigate(`/chat/${item.id}`)}
                >
                  <span className="block truncate text-xs font-medium text-ink">
                    {item.title || "New conversation"}
                  </span>
                  <span className="mt-0.5 block text-[10px] text-muted">
                    {formatDate(item.updated_at)}
                  </span>
                </button>
                <button
                  type="button"
                  aria-label="Delete conversation"
                  className="mr-1 rounded-lg p-1.5 text-muted opacity-0 transition group-hover:opacity-100 focus:opacity-100 hover:bg-danger/10 hover:text-danger"
                  onClick={() => {
                    if (window.confirm("Delete this conversation?")) {
                      removeConversation.mutate(item.id);
                    }
                  }}
                >
                  <CloseIcon className="size-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      </aside>

      <section className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex min-h-[66px] items-center justify-between gap-3 border-b border-line px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              variant="ghost"
              className="size-10 shrink-0 px-0"
              aria-label={libraryOpen ? "Hide conversation panel" : "Show conversation panel"}
              aria-expanded={libraryOpen}
              title={libraryOpen ? "Hide conversation panel" : "Show conversation panel"}
              onClick={() => setLibraryOpen((open) => !open)}
            >
              <PanelIcon className="size-[22px]" />
            </Button>
            <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary-soft text-primary">
              <ChatIcon className="size-[17px]" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-[13px] font-semibold text-ink">
                {activeConversation?.title || "New conversation"}
              </p>
              <p className="truncate text-[11px] text-muted">
                {activeConversation
                  ? `${count} messages${kbName ? ` · ${kbName}` : ""}`
                  : kbName || "Grounded answers from your documents"}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <div className="lg:hidden">
              <KnowledgeBasePicker
                knowledgeBases={kbs.data ?? []}
                selectedId={kbId}
                onSelect={selectKnowledgeBase}
                className="max-w-36 sm:max-w-48"
              />
            </div>
            <select
              className="max-w-36 cursor-pointer rounded-xl border border-line bg-surface px-2.5 py-2 text-xs font-medium text-ink outline-none transition hover:bg-elevated focus:border-primary/60 focus:ring-2 focus:ring-primary/15 sm:max-w-52"
              value={model}
              onChange={(event) => changeModel(event.target.value)}
              aria-label="Chat model"
            >
              {!model ? (
                <option value="">{models.data ? "Choose model" : "Loading models…"}</option>
              ) : null}
              {models.data && !models.data.chat.some((item) => item.name === model) && model ? (
                <option value={model}>{model} (not installed)</option>
              ) : null}
              {(models.data?.chat ?? []).map((item) => (
                <option key={item.name} value={item.name}>{item.name}</option>
              ))}
            </select>
          </div>
        </header>

        <div className="relative min-h-0 flex-1">
          <div
            ref={messageListRef}
            onScroll={handleMessageScroll}
            className="h-full overflow-y-auto px-4 py-6 sm:px-7"
          >
          <div className="mx-auto flex min-h-full w-full max-w-[760px] flex-col gap-7">
            {error ? <Banner>{error}</Banner> : null}

            {noKbs ? (
              <div className="my-auto flex flex-col items-center rounded-3xl border border-line bg-elevated/40 px-6 py-12 text-center">
                <span className="grid size-14 place-items-center rounded-2xl bg-primary-soft text-primary">
                  <DatabaseIcon className="size-6" />
                </span>
                <h1 className="mt-5 text-xl font-semibold tracking-tight text-ink">
                  Start with a knowledge base
                </h1>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-muted">
                  Add your documents, and Local RAG will find relevant passages and cite them in every answer.
                </p>
                <Link
                  to="/kb"
                  className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-on-primary transition hover:bg-primary-hover"
                >
                  <PlusIcon /> Create a knowledge base
                </Link>
              </div>
            ) : null}

            {!noKbs && messages.length === 0 && !stream ? (
              <div className="my-auto py-6">
                <div className="mx-auto max-w-xl text-center">
                  <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-primary-soft text-primary">
                    <ChatIcon className="size-[21px]" />
                  </span>
                  <p className="mt-5 text-[11px] font-semibold tracking-[0.16em] text-primary uppercase">
                    Your private research assistant
                  </p>
                  <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-ink sm:text-[38px]">
                    Ask your documents.
                  </h1>
                  <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-muted">
                    Search across your sources, get a clear answer, and follow every citation back to the original passage.
                  </p>

                  {selectedKb?.document_count ? (
                    <div className="mt-7 flex flex-wrap items-center justify-center gap-2 text-xs text-muted">
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5">
                        <span className="size-1.5 rounded-full bg-success" />
                        {selectedKb.name}
                      </span>
                      <span>{selectedKb.document_count} source{selectedKb.document_count === 1 ? "" : "s"} indexed</span>
                    </div>
                  ) : selectedKb ? (
                    <Link
                      to={`/kb/${selectedKb.id}`}
                      className="mt-7 inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3.5 py-2 text-xs font-medium text-primary transition hover:border-primary/30 hover:bg-primary-soft"
                    >
                      <PlusIcon className="size-3.5" /> Add documents to {selectedKb.name}
                    </Link>
                  ) : null}
                </div>

                <div className="mx-auto mt-9 grid max-w-2xl gap-2.5 sm:grid-cols-2">
                  {[
                    "What are the key ideas in these documents?",
                    "Summarize the main points for me",
                    "What evidence supports the central claim?",
                    "Compare the different perspectives",
                  ].map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => setDraft(prompt)}
                      className="rounded-2xl border border-line bg-surface px-4 py-3 text-left text-xs leading-relaxed text-ink-soft transition hover:border-primary/35 hover:bg-primary-soft/50"
                    >
                      <span className="mb-1.5 block text-[10px] font-semibold tracking-wide text-muted uppercase">
                        Try asking
                      </span>
                      {prompt}
                    </button>
                  ))}
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
              <div className="animate-rise flex gap-3">
                <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-xl bg-primary text-on-primary">
                  <DatabaseIcon className="size-4" />
                </span>
                <div className="min-w-0 flex-1 space-y-3 pt-1">
                  {stream.rewritten ? (
                    <p className="text-xs text-muted">
                      Searching for <span className="font-medium text-primary">{stream.rewritten}</span>
                    </p>
                  ) : null}

                  {stream.sources.length > 0 ? (
                    <button
                      type="button"
                      onClick={() => setCitations({ sources: stream.sources, active: stream.sources[0].n })}
                      className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-2.5 py-1 text-[11px] font-medium text-primary"
                    >
                      <FileIcon className="size-3.5" /> {stream.sources.length} sources found
                    </button>
                  ) : null}
                  {stream.thinking ? <ThinkingBlock thinking={stream.thinking} /> : null}
                  {stream.text ? (
                    <AnswerMarkdown
                      text={stream.text}
                      onCite={(n) => setCitations({ sources: stream.sources, active: n })}
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-sm text-muted">
                      <Spinner /> Searching your sources…
                    </div>
                  )}
                  {stopped ? <Badge tone="warn">Generation stopped</Badge> : null}
                </div>
              </div>
            ) : null}

          </div>
          </div>
          {!isAtBottom && messages.length > 0 ? (
            <button
              type="button"
              onClick={scrollToLatest}
              className="absolute bottom-4 right-5 z-10 inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3.5 py-2 text-xs font-medium text-ink shadow-lg transition hover:border-primary/40 hover:bg-elevated"
              aria-label="Scroll to latest message"
            >
              <ArrowDownIcon className="size-4" />
              Back to latest
            </button>
          ) : null}
        </div>

        <footer className="border-t border-line bg-surface/80 px-4 py-3.5 sm:px-7">
          <div className="mx-auto w-full max-w-[760px]">
            <div className="rounded-2xl border border-line bg-surface shadow-[0_5px_24px_-16px_rgb(35_55_90_/_0.18)] transition focus-within:border-primary/45 focus-within:ring-4 focus-within:ring-primary/10">
              <textarea
                className="max-h-40 min-h-[54px] w-full resize-none bg-transparent px-4 pt-3.5 text-sm text-ink outline-none placeholder:text-muted/75 disabled:opacity-60"
                placeholder={kbName ? `Ask a question about ${kbName}…` : "Ask a question about your sources…"}
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
              <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5 pl-3">
                <div className="flex min-w-0 items-center gap-1.5">
                  <Button
                    variant="ghost"
                    className={cx(
                      "h-8 shrink-0 gap-2 rounded-lg px-2 text-sm text-ink-soft hover:bg-elevated hover:text-ink",
                      think && "bg-accent/10 text-accent hover:bg-accent/15 hover:text-accent",
                    )}
                    aria-label="Reasoning mode"
                    aria-pressed={think}
                    title="Toggle reasoning mode"
                    onClick={() => {
                      const enabled = !think;
                      setThink(enabled);
                      remember("rag.think", String(enabled));
                    }}
                  >
                    <BrainIcon className="size-5" />
                    <span>Think</span>
                  </Button>
                  <div className="relative shrink-0">
                    <select
                      className="h-8 w-[104px] cursor-pointer appearance-none rounded-lg border border-line bg-elevated py-1 pl-2.5 pr-7 text-xs font-medium text-ink outline-none transition hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-primary/40"
                      aria-label="Answer length"
                      title="Choose answer length"
                      value={answerLength}
                      onChange={(event) => {
                        const next = answerLengthValue(event.target.value);
                        setAnswerLength(next);
                        remember(ANSWER_LENGTH_KEY, next);
                      }}
                    >
                      <option value="short">Short</option>
                      <option value="balanced">Balanced</option>
                      <option value="detailed">Detailed</option>
                    </select>
                    <ChevronDownIcon className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-muted" />
                  </div>
                  <p className="flex min-w-0 items-center gap-1.5 truncate text-[10px] text-muted">
                    <span className="size-1.5 shrink-0 rounded-full bg-success" />
                    <span className="truncate">Grounded in {kbName || "your selected sources"}</span>
                  </p>
                </div>
                {stream ? (
                  <Button
                    variant="danger"
                    className="size-10 shrink-0 rounded-xl px-0"
                    onClick={() => abortRef.current?.abort()}
                    aria-label="Stop generating"
                    title="Stop generating"
                  >
                    <StopIcon />
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    className="size-10 shrink-0 rounded-xl px-0"
                    onClick={() => void send()}
                    disabled={!draft.trim() || !model || noKbs}
                    title={!model ? "Waiting for the model list" : "Send message"}
                    aria-label="Send"
                  >
                    <SendIcon className="size-7" />
                  </Button>
                )}
              </div>
            </div>
            <p className="mt-2 text-center text-[10px] text-muted">
              Answers are based on your sources · Enter to send, Shift+Enter for a new line
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
        <div className="max-w-[88%] rounded-2xl rounded-br-md bg-elevated px-4 py-3 text-sm leading-relaxed text-ink sm:max-w-[80%]">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-rise flex gap-3">
      <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-xl bg-primary text-on-primary">
        <DatabaseIcon className="size-4" />
      </span>
      <div className="min-w-0 flex-1 space-y-2.5 pt-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-ink">Local RAG</span>
          <span className="text-[10px] text-muted">{message.model_used}</span>
        </div>
        {message.thinking ? <ThinkingBlock thinking={message.thinking} /> : null}
        <AnswerMarkdown text={message.content} onCite={onCite} />

        {message.sources.length > 0 ? (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {message.sources.map((source) => (
              <button
                key={source.n}
                type="button"
                onClick={() => onCite(source.n)}
                className="inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1.5 text-[10px] font-medium text-ink-soft transition hover:border-primary/35 hover:bg-primary-soft"
              >
                <span className="grid size-4 place-items-center rounded-full bg-primary-soft text-[9px] font-bold text-primary">
                  {source.n}
                </span>
                <span className="max-w-40 truncate">
                  {source.document || "Source"}
                  {source.page !== null ? ` · p.${source.page}` : ""}
                </span>
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
