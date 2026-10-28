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
      {busy ? <Spinner /> : null}
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
    // Keep polling while the worker is chewing on something.
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
      <div className="flex items-center gap-2 text-sm text-slate-400">
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
        <Link to="/kb" className="text-sm text-indigo-300 hover:text-indigo-200">
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
        <Link to="/kb" className="text-sm text-slate-400 hover:text-slate-200">
          ← Knowledge bases
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-white">{data.name}</h1>
            <p className="text-sm text-slate-400">{data.description || "No description"}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge>{data.document_count} documents</Badge>
            <Badge tone={data.is_locked ? "info" : "neutral"}>
              {data.is_locked ? "embedding locked" : "embedding editable"}
            </Badge>
          </div>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          {data.embedding_model} · {data.chunk_size} chars per chunk,{" "}
          {data.chunk_overlap} overlap
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
          "flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition",
          dragging
            ? "border-indigo-500 bg-indigo-500/10"
            : "border-slate-800 bg-slate-900/40",
        )}
      >
        <p className="text-sm text-slate-300">
          Drop files here, or{" "}
          <button
            type="button"
            className="font-medium text-indigo-300 underline-offset-2 hover:underline"
            onClick={() => fileInput.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="text-xs text-slate-500">
          PDF, Word, Markdown or plain text · up to 50 MB each
        </p>
        {uploading > 0 ? (
          <p className="flex items-center gap-2 text-xs text-indigo-300">
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
          title="No documents yet"
          hint="Upload a PDF, Word file, Markdown or text file to start indexing."
        />
      ) : null}

      {list.length > 0 ? (
        <Card className="overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Size</th>
                <th className="px-4 py-3 font-medium">Chunks</th>
                <th className="px-4 py-3 font-medium">Added</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {list.map((doc) => (
                <tr key={doc.id} className="align-top">
                  <td className="max-w-xs px-4 py-3">
                    <p className="truncate text-slate-200" title={doc.original_name}>
                      {doc.original_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {doc.file_type.toUpperCase()}
                      {doc.page_count ? ` · ${doc.page_count} pages` : ""}
                    </p>
                    {doc.status === "failed" && doc.error ? (
                      <p className="mt-1 rounded bg-red-500/10 px-2 py-1 text-xs text-red-300">
                        {doc.error}
                      </p>
                    ) : null}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge doc={doc} />
                  </td>
                  <td className="px-4 py-3 text-slate-400">{formatBytes(doc.size_bytes)}</td>
                  <td className="px-4 py-3 text-slate-400">{doc.chunk_count || "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{formatDate(doc.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="danger"
                      disabled={remove.isPending}
                      onClick={() => {
                        if (window.confirm(`Remove "${doc.original_name}"?`)) {
                          remove.mutate(doc.id);
                        }
                      }}
                    >
                      Delete
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
