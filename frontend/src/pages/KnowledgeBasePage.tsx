import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ApiError,
  deleteDocument,
  getKnowledgeBase,
  listDocuments,
  uploadDocument,
} from "../api/client";
import type { Document } from "../api/types";
import { cx, formatBytes, formatDate } from "../lib/format";
import { FileIcon, TrashIcon, UploadIcon } from "../components/icons";
import { Badge, Banner, Button, Card, EmptyState, Spinner } from "../components/ui";

const ACCEPTED = [".pdf", ".txt", ".text", ".log", ".md", ".markdown", ".docx"];

function StatusBadge({ doc }: { doc: Document }) {
  const busy = doc.status === "pending" || doc.status === "processing";
  const tone =
    doc.status === "ready"
      ? "ok"
      : doc.status === "failed"
        ? "bad"
        : doc.status === "processing"
          ? "info"
          : "warn";
  const label =
    doc.status === "pending"
      ? "Queued"
      : doc.status === "processing"
        ? "Processing"
        : doc.status === "ready"
          ? "Ready"
          : "Failed";

  return (
    <Badge tone={tone}>
      {busy ? <Spinner /> : <span className="size-1.5 rounded-full bg-current" />}
      {label}
    </Badge>
  );
}

export default function KnowledgeBasePage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const kb = useQuery({
    queryKey: ["kb", id],
    queryFn: () => getKnowledgeBase(id),
    enabled: Boolean(id),
  });

  const documents = useQuery({
    queryKey: ["docs", id],
    queryFn: () => listDocuments(id),
    enabled: Boolean(id),
    // Keep polling while files are processing.
    refetchInterval: (query) =>
      query.state.data?.some(
        (doc) => doc.status === "pending" || doc.status === "processing",
      )
        ? 1500
        : false,
  });

  const remove = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["docs", id] });
      queryClient.invalidateQueries({ queryKey: ["kbs"] });
    },
    onError: (err) =>
      setUploadError(err instanceof ApiError ? err.message : "Could not delete that file."),
  });

  async function addFiles(files: File[]) {
    if (files.length === 0) return;
    setUploadError(null);
    setUploading(files.length);
    const problems: string[] = [];

    for (const file of files) {
      const suffix = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
      if (!ACCEPTED.includes(suffix)) {
        problems.push(`${file.name}: that file type is not supported.`);
      } else {
        try {
          await uploadDocument(id, file);
        } catch (err) {
          problems.push(
            `${file.name}: ${err instanceof ApiError ? err.message : "upload failed."}`,
          );
        }
      }
      setUploading((count) => count - 1);
    }

    await queryClient.invalidateQueries({ queryKey: ["docs", id] });
    await queryClient.invalidateQueries({ queryKey: ["kbs"] });
    if (problems.length > 0) setUploadError(problems.join("\n"));
  }

  if (kb.isPending) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted">
        <Spinner /> Loading…
      </div>
    );
  }

  if (kb.isError || !kb.data) {
    return (
      <div className="space-y-4">
        <Banner>
          {kb.error instanceof ApiError ? kb.error.message : "That knowledge base is gone."}
        </Banner>
        <Link to="/kb" className="text-sm font-medium text-primary hover:text-primary-hover">
          ← Back to knowledge bases
        </Link>
      </div>
    );
  }

  const data = kb.data;
  const list = documents.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/kb"
          className="text-sm text-muted transition hover:text-ink"
        >
          ← Knowledge bases
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{data.name}</h1>
            <p className="mt-1 text-sm text-muted">{data.description || "No description"}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge>
              {data.document_count} document{data.document_count === 1 ? "" : "s"}
            </Badge>
            <Badge tone={data.is_locked ? "info" : "neutral"}>
              {data.is_locked ? "embedding locked" : "embedding editable"}
            </Badge>
          </div>
        </div>
        <p className="mt-2 text-xs text-muted">
          {data.embedding_model} · {data.chunk_size} chars per chunk, {data.chunk_overlap}{" "}
          overlap
        </p>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          void addFiles(Array.from(event.dataTransfer.files));
        }}
        className={cx(
          "flex flex-col items-center justify-center gap-2.5 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition",
          dragging
            ? "border-primary/60 bg-primary/5"
            : "border-line bg-app/40 hover:border-primary/40",
        )}
      >
        <span
          className={cx(
            "grid size-10 place-items-center rounded-xl transition",
            dragging ? "bg-primary/15 text-primary" : "bg-elevated text-muted",
          )}
        >
          <UploadIcon className="size-5" />
        </span>
        <p className="text-sm text-ink">
          Drop files here, or{" "}
          <button
            type="button"
            className="cursor-pointer font-medium text-primary underline-offset-2 hover:underline"
            onClick={() => fileInput.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="text-xs text-muted">PDF, Word, Markdown or plain text · up to 50 MB each</p>
        {uploading > 0 ? (
          <p className="flex items-center gap-2 text-xs font-medium text-primary">
            <Spinner /> Uploading {uploading} file{uploading === 1 ? "" : "s"}…
          </p>
        ) : null}
        <input
          ref={fileInput}
          type="file"
          multiple
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(event) => {
            void addFiles(Array.from(event.target.files ?? []));
            event.target.value = "";
          }}
        />
      </div>

      {uploadError ? (
        <Banner>
          {uploadError.split("\n").map((line) => (
            <p key={line}>{line}</p>
          ))}
        </Banner>
      ) : null}

      {documents.isError ? (
        <Banner>
          {documents.error instanceof ApiError
            ? documents.error.message
            : "Could not load documents."}
        </Banner>
      ) : null}

      {documents.isSuccess && list.length === 0 ? (
        <EmptyState
          icon={<FileIcon className="size-5" />}
          title="No documents yet"
          hint="Upload a PDF, Word file, Markdown or text file to start indexing."
        />
      ) : null}

      {list.length > 0 ? (
        <Card className="overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-app/40 text-[11px] tracking-wide text-muted uppercase">
              <tr>
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Chunks</th>
                <th className="px-4 py-3 font-medium">Added</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line/70">
              {list.map((doc) => (
                <tr key={doc.id} className="align-top transition hover:bg-elevated/40">
                  <td className="max-w-xs px-4 py-3">
                    <div className="flex items-start gap-2.5">
                      <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-elevated text-muted">
                        <FileIcon className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <p
                          className="truncate font-medium text-ink"
                          title={doc.original_name}
                        >
                          {doc.original_name}
                        </p>
                        <p className="text-xs text-muted">
                          {doc.file_type.toUpperCase()} · {formatBytes(doc.size_bytes)}
                          {doc.page_count ? ` · ${doc.page_count} pages` : ""}
                        </p>
                        {doc.status === "failed" && doc.error ? (
                          <p className="mt-1 rounded-lg bg-danger/10 px-2 py-1 text-xs text-danger">
                            {doc.error}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge doc={doc} />
                  </td>
                  <td className="px-4 py-3 text-muted">{doc.chunk_count || "—"}</td>
                  <td className="px-4 py-3 text-muted">{formatDate(doc.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="ghost"
                      className="px-2 text-muted hover:text-danger"
                      aria-label={`Delete ${doc.original_name}`}
                      disabled={remove.isPending}
                      onClick={() => {
                        if (window.confirm(`Remove "${doc.original_name}"?`)) {
                          remove.mutate(doc.id);
                        }
                      }}
                    >
                      <TrashIcon />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}
