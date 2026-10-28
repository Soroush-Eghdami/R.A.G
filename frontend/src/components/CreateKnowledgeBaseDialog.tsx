import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { ApiError, createKnowledgeBase, getSettings } from "../api/client";
import { useModels } from "../lib/hooks";
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
    if (!open) return;
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, [open]);

  // Pick a sensible default once the model list arrives.
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
    onError: (err) => setError(err instanceof ApiError ? err.message : "Something went wrong."),
  });

  const close = () => {
    setError(null);
    onClose();
  };

  return (
    <dialog
      ref={dialogRef}
      onClose={close}
      onCancel={close}
      className="w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-0 text-slate-100 backdrop:bg-slate-950/70"
    >
      <form
        className="space-y-4 p-6"
        onSubmit={(event) => {
          event.preventDefault();
          if (!model) {
            setError("Pick an embedding model first.");
            return;
          }
          create.mutate();
        }}
      >
        <div>
          <h2 className="text-lg font-semibold">New knowledge base</h2>
          <p className="text-sm text-slate-400">
            One collection of documents you can ask questions about.
          </p>
        </div>

        {error ? <Banner>{error}</Banner> : null}

        {models.isError ? (
          <Banner tone="warn">
            Can't list embedding models. Is Ollama running? Pull one with{" "}
            <code className="rounded bg-slate-800 px-1">ollama pull nomic-embed-text</code>.
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
            {embeddingModels.length === 0 ? <option value="">No embedding models</option> : null}
            {embeddingModels.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
                {item.parameter_size ? ` · ${item.parameter_size}` : ""}
              </option>
            ))}
          </select>
        </Field>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={create.isPending || !name.trim()}>
            {create.isPending ? <Spinner /> : null}
            Create
          </Button>
        </div>
      </form>
    </dialog>
  );
}
