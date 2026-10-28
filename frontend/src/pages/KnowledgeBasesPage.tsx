import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiError,
  deleteKnowledgeBase,
  listKnowledgeBases,
} from "../api/client";
import { useModels } from "../lib/hooks";
import { formatDate } from "../lib/format";
import CreateKnowledgeBaseDialog from "../components/CreateKnowledgeBaseDialog";
import { Badge, Banner, Button, Card, EmptyState, Spinner } from "../components/ui";

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

  const ollamaDown = models.isError;

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Knowledge bases</h1>
          <p className="text-sm text-slate-400">
            Upload documents, then ask questions about them.
          </p>
        </div>
        <Button variant="primary" onClick={() => setCreating(true)}>
          New knowledge base
        </Button>
      </header>

      {error ? <Banner>{error}</Banner> : null}

      {ollamaDown ? (
        <Banner tone="warn">
          Ollama is not reachable, so new knowledge bases can't pick an embedding model.
          Start it and refresh.
        </Banner>
      ) : null}

      {kbs.isPending ? (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner /> Loading…
        </div>
      ) : null}

      {kbs.isError ? (
        <Banner>{kbs.error instanceof ApiError ? kbs.error.message : "Could not load."}</Banner>
      ) : null}

      {kbs.data && kbs.data.length === 0 ? (
        <EmptyState
          title="No knowledge bases yet"
          hint="A knowledge base holds the documents you want to ask about. Create one, then drag in a PDF."
          action={
            <Button variant="primary" onClick={() => setCreating(true)}>
              Create the first one
            </Button>
          }
        />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {kbs.data?.map((kb) => (
          <Card key={kb.id} className="flex flex-col gap-3 transition hover:border-slate-700">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Link
                  to={`/kb/${kb.id}`}
                  className="block truncate text-base font-medium text-white hover:text-indigo-300"
                >
                  {kb.name}
                </Link>
                <p className="line-clamp-2 text-sm text-slate-400">
                  {kb.description || "No description"}
                </p>
              </div>
              {kb.is_locked ? <Badge tone="info">locked</Badge> : null}
            </div>

            <dl className="grid grid-cols-2 gap-2 text-xs text-slate-400">
              <div>
                <dt className="text-slate-500">Documents</dt>
                <dd className="text-slate-200">{kb.document_count}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Created</dt>
                <dd className="text-slate-200">{formatDate(kb.created_at)}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-slate-500">Embedding model</dt>
                <dd className="truncate text-slate-200">{kb.embedding_model}</dd>
              </div>
            </dl>

            <div className="mt-auto flex items-center justify-between gap-2">
              <Link
                to={`/kb/${kb.id}`}
                className="text-sm font-medium text-indigo-300 hover:text-indigo-200"
              >
                Open →
              </Link>
              <Button
                variant="danger"
                onClick={() => {
                  if (window.confirm(`Delete "${kb.name}" and all its documents?`)) {
                    remove.mutate(kb.id);
                  }
                }}
                disabled={remove.isPending}
              >
                Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <CreateKnowledgeBaseDialog open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
