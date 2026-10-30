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
    <div className="space-y-6">
      <PageHeader
        title="Knowledge bases"
        subtitle="Upload documents, then ask questions about them."
        actions={
          <Button variant="primary" onClick={() => setCreating(true)}>
            <PlusIcon />
            New knowledge base
          </Button>
        }
      />

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
          hint="A knowledge base holds the documents you want to ask about. Create one, then drag in a PDF."
          action={
            <Button variant="primary" onClick={() => setCreating(true)}>
              <PlusIcon />
              Create the first one
            </Button>
          }
        />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {kbs.data?.map((kb) => (
          <Card
            key={kb.id}
            className="group flex flex-col gap-4 transition hover:border-primary/40 hover:shadow-md"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                  <LibraryIcon className="size-[18px]" />
                </span>
                <div className="min-w-0">
                  <Link
                    to={`/kb/${kb.id}`}
                    className="block truncate text-base font-semibold text-ink transition group-hover:text-primary"
                  >
                    {kb.name}
                  </Link>
                  <p className="line-clamp-2 text-sm text-muted">
                    {kb.description || "No description"}
                  </p>
                </div>
              </div>
              {kb.is_locked ? <Badge tone="info">locked</Badge> : null}
            </div>

            <div className="flex flex-wrap gap-1.5">
              <Badge>{kb.document_count} document{kb.document_count === 1 ? "" : "s"}</Badge>
              <Badge className="max-w-full truncate">{kb.embedding_model}</Badge>
            </div>

            <div className="mt-auto flex items-center justify-between gap-2 border-t border-line pt-3">
              <span className="text-xs text-muted">Created {formatDate(kb.created_at)}</span>
              <div className="flex items-center gap-1">
                <Link
                  to={`/kb/${kb.id}`}
                  className="rounded-lg px-2.5 py-1.5 text-sm font-medium text-primary transition hover:bg-primary/10"
                >
                  Open →
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
