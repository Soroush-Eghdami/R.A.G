import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { ApiError, createKnowledgeBase, getSettings } from "../api/client";
import { useModels } from "../lib/hooks";
import { CloseIcon, PlusIcon } from "./icons";
import { Banner, Button, Field, Spinner, inputClass } from "./ui";

type Props = { open: boolean; onClose: () => void };

export default function CreateKnowledgeBaseDialog({ open, onClose }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const queryClient = useQueryClient();
  const models = useModels();
  const settings = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [model, setModel] = useState("");
  const [error, setError] = useState<string | null>(null);

  const embeddingModels = models.data?.embedding ?? [];
  const preferred = settings.data?.default_embedding_model ?? "";

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  // Select a default when models load.
  useEffect(() => {
    if (model || embeddingModels.length === 0) return;
    const match = embeddingModels.find((item) => item.name === preferred);
    setModel(match?.name ?? embeddingModels[0].name);
  }, [embeddingModels, model, preferred]);

  const create = useMutation({
    mutationFn: () => createKnowledgeBase({ name, description, embedding_model: model }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["kbs"] });
      setName("");
      setDescription("");
      setModel("");
      setError(null);
      onClose();
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.message : "Something went wrong."),
  });

  const dismiss = () => {
    setError(null);
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      onClose={() => setError(null)}
      onCancel={(event) => {
        event.preventDefault();
        dismiss();
      }}
      className="fixed left-1/2 top-1/2 m-0 max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-3xl border border-line bg-surface p-0 text-ink shadow-2xl"
    >
      <form
        className="space-y-5 p-7"
        onSubmit={(event) => {
          event.preventDefault();
          if (!model) {
            setError("Pick an embedding model first.");
            return;
          }
          create.mutate();
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-ink">
              New knowledge base
            </h2>
            <p className="text-sm text-muted">
              One collection of documents you can ask questions about.
            </p>
          </div>
          <Button type="button" variant="ghost" className="px-2" onClick={dismiss} aria-label="Close">
            <CloseIcon />
          </Button>
        </div>

        {error ? <Banner>{error}</Banner> : null}

        {models.isError ? (
          <Banner tone="warn">
            Can't load model configuration. Check your llama.cpp setup and start the embedding server with{" "}
            <code className="rounded bg-app px-1.5 py-0.5 font-mono text-xs">
              .\scripts\start-llama.ps1 -Mode embedding
            </code>
            .
          </Banner>
        ) : null}

        <Field label="Name">
          <input
            className={inputClass}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Product docs"
            required
            maxLength={200}
            autoFocus
          />
        </Field>

        <Field label="Description" hint="Optional. What lives in here?">
          <textarea
            className={inputClass}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={2}
            placeholder="Manuals, specs and release notes"
          />
        </Field>

        <Field
          label="Embedding model"
          hint="Locked once a document is indexed. Changing it later means a new knowledge base."
        >
          <select
            className={inputClass}
            value={model}
            onChange={(event) => setModel(event.target.value)}
            disabled={models.isPending || embeddingModels.length === 0}
          >
            {embeddingModels.length === 0 ? (
              <option value="">No embedding models</option>
            ) : null}
            {embeddingModels.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
                {item.parameter_size ? ` · ${item.parameter_size}` : ""}
              </option>
            ))}
          </select>
        </Field>

        <div className="flex justify-end gap-2 border-t border-line pt-4">
          <Button type="button" variant="ghost" onClick={dismiss}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={create.isPending || !name.trim()}>
            {create.isPending ? <Spinner /> : <PlusIcon />}
            Create
          </Button>
        </div>
      </form>
    </dialog>
  );
}
