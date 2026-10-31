import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, deleteKnowledgeBase, listKnowledgeBases } from "../api/client";
import { useModels } from "../lib/hooks";
import { formatDate } from "../lib/format";
import CreateKnowledgeBaseDialog from "../components/CreateKnowledgeBaseDialog";
import { DatabaseIcon, LibraryIcon, PlusIcon, TrashIcon } from "../components/icons";
import {
  Badge,
  Banner,
  Button,
  Card,
  EmptyState,
  PageHeader,
  Spinner,
} from "../components/ui";

export default function KnowledgeBasesPage() {
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const kbs = useQuery({ queryKey: ["kbs"], queryFn: listKnowledgeBases });
  const models = useModels();

  const remove = useMutation({
    mutationFn: deleteKnowledgeBase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["kbs"] }),
    onError: (err) =>
      setError(err instanceof ApiError ? err.message : "Could not delete that."),
  });

  return (
    <div className="mx-auto w-full max-w-6xl space-y-7 px-4 py-6 md:px-3 md:py-3">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          title="Your knowledge"
          subtitle="Bring your documents together. Ask questions and get answers linked to the source."
        />
        <Button variant="primary" className="rounded-xl px-4 py-2.5" onClick={() => setCreating(true)}>
          <PlusIcon />
          New collection
        </Button>
      </div>

      {kbs.data && kbs.data.length > 0 ? (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-y border-line py-3.5 text-xs text-muted">
          <span>
            <strong className="font-semibold text-ink">{kbs.data.length}</strong>{" "}
            collection{kbs.data.length === 1 ? "" : "s"}
          </span>
          <span>
            <strong className="font-semibold text-ink">
              {kbs.data.reduce((total, kb) => total + kb.document_count, 0)}
            </strong>{" "}
            documents indexed
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-success" />
            Private and local
          </span>
        </div>
      ) : null}

      {error ? <Banner>{error}</Banner> : null}

      {models.isError ? (
        <Banner tone="warn">
          Model configuration could not be loaded. Check the backend and llama.cpp setup.
        </Banner>
      ) : null}

      {kbs.isPending ? (
        <div className="flex items-center gap-2 text-sm text-muted">
          <Spinner /> Loading…
        </div>
      ) : null}

      {kbs.isError ? (
        <Banner>{kbs.error instanceof ApiError ? kbs.error.message : "Could not load."}</Banner>
      ) : null}

      {kbs.data && kbs.data.length === 0 ? (
        <EmptyState
          icon={<DatabaseIcon className="size-5" />}
          title="No knowledge bases yet"
          hint="Create a collection for a project, add your documents, and ask questions with source-backed answers."
          action={
            <Button variant="primary" onClick={() => setCreating(true)}>
              <PlusIcon />
              Create a collection
            </Button>
          }
        />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {kbs.data?.map((kb) => (
          <Card
            key={kb.id}
            className="group flex min-h-56 flex-col gap-4 transition duration-200 hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-[0_14px_35px_-24px_rgb(48_72_120_/_0.24)]"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-[14px] bg-primary-soft text-primary">
                  <LibraryIcon className="size-[18px]" />
                </span>
                <div className="min-w-0">
                  <Link
                    to={`/kb/${kb.id}`}
                    className="block truncate text-[15px] font-semibold tracking-tight text-ink transition group-hover:text-primary"
                  >
                    {kb.name}
                  </Link>
                  <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted">
                    {kb.description || "No description"}
                  </p>
                </div>
              </div>
              {kb.is_locked ? <Badge tone="info">locked</Badge> : null}
            </div>

            <div className="flex items-center gap-2 rounded-xl bg-elevated/65 px-3 py-2.5">
              <span className="grid size-7 place-items-center rounded-lg bg-surface text-primary">
                <DatabaseIcon className="size-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-ink">
                  {kb.document_count} <span className="font-normal text-muted">source{kb.document_count === 1 ? "" : "s"}</span>
                </p>
                <p className="text-[10px] text-muted">Embedding · {kb.embedding_model}</p>
              </div>
            </div>

            <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-3">
              <span className="text-[11px] text-muted">Created {formatDate(kb.created_at)}</span>
              <div className="flex items-center gap-1">
                <Link
                  to={`/kb/${kb.id}`}
                  className="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-primary transition hover:bg-primary-soft"
                >
                  Open collection →
                </Link>
                <Button
                  variant="ghost"
                  className="px-2 text-muted hover:text-danger"
                  aria-label={`Delete ${kb.name}`}
                  onClick={() => {
                    if (window.confirm(`Delete "${kb.name}" and all its documents?`)) {
                      remove.mutate(kb.id);
                    }
                  }}
                  disabled={remove.isPending}
                >
                  <TrashIcon />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <CreateKnowledgeBaseDialog open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
