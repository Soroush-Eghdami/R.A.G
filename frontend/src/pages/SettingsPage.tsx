import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ApiError, getSettings, updateSettings } from "../api/client";
import type { AppSettings } from "../api/types";
import { useHealth, useModels } from "../lib/hooks";
import {
  Badge,
  Banner,
  Button,
  Card,
  Field,
  Spinner,
  inputClass,
} from "../components/ui";

const CONTEXT_SIZES = [2048, 4096, 8192, 16384, 32768];

function ModelSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { name: string; parameter_size: string }[];
  placeholder: string;
}) {
  const known = options.some((option) => option.name === value);
  return (
    <select className={inputClass} value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="">{placeholder}</option>
      {!known && value ? <option value={value}>{value} (not installed)</option> : null}
      {options.map((option) => (
        <option key={option.name} value={option.name}>
          {option.name}
          {option.parameter_size ? ` · ${option.parameter_size}` : ""}
        </option>
      ))}
    </select>
  );
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const health = useHealth();
  const models = useModels();
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [form, setForm] = useState<AppSettings | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settingsQuery.data) setForm(settingsQuery.data);
  }, [settingsQuery.data]);

  const save = useMutation({
    mutationFn: (patch: Partial<AppSettings>) => updateSettings(patch),
    onSuccess: (data) => {
      setForm(data);
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      window.setTimeout(() => setSaved(false), 2500);
    },
  });

  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setForm((current) => (current ? { ...current, [key]: value } : current));
    setSaved(false);
  };

  const online = health.data?.ollama.reachable ?? false;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Settings</h1>
        <p className="text-sm text-slate-400">
          Connection status and the defaults new chats start from.
        </p>
      </header>

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-medium text-white">Ollama</h2>
          <Button
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ["health"] });
              queryClient.invalidateQueries({ queryKey: ["models"] });
            }}
          >
            Recheck
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={online ? "ok" : "bad"}>
            <span
              className={`size-1.5 rounded-full ${online ? "bg-emerald-400" : "bg-red-400"}`}
            />
            {online ? "reachable" : "offline"}
          </Badge>
          {health.data?.ollama.version ? (
            <Badge>v{health.data.ollama.version}</Badge>
          ) : null}
          <Badge tone={health.data?.database.ok ? "ok" : "bad"}>
            database {health.data?.database.ok ? "ok" : "down"}
          </Badge>
        </div>

        <p className="break-all text-sm text-slate-400">
          {health.data?.ollama.base_url ?? "…"}
        </p>

        {!online && health.data?.ollama.error ? (
          <Banner tone="warn">{health.data.ollama.error}</Banner>
        ) : null}

        {models.data ? (
          <p className="text-xs text-slate-500">
            {models.data.chat.length} chat models, {models.data.embedding.length} embedding
            models
            {models.data.cloud_hidden > 0
              ? ` · ${models.data.cloud_hidden} cloud model(s) hidden`
              : ""}
          </p>
        ) : null}
      </Card>

      <Card className="space-y-5">
        <div>
          <h2 className="text-base font-medium text-white">Defaults</h2>
          <p className="text-sm text-slate-400">
            Used when a conversation or knowledge base does not pick its own.
          </p>
        </div>

        {settingsQuery.isError ? (
          <Banner>
            {settingsQuery.error instanceof ApiError
              ? settingsQuery.error.message
              : "Could not load settings."}
          </Banner>
        ) : null}

        {save.isError ? (
          <Banner>
            {save.error instanceof ApiError ? save.error.message : "Could not save."}
          </Banner>
        ) : null}

        {!form ? (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Spinner /> Loading…
          </div>
        ) : (
          <form
            className="space-y-5"
            onSubmit={(event) => {
              event.preventDefault();
              save.mutate({
                default_chat_model: form.default_chat_model,
                default_embedding_model: form.default_embedding_model,
                top_k: form.top_k,
                temperature: form.temperature,
                num_ctx: form.num_ctx,
              });
            }}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Default chat model" hint="Conversations can still pick their own.">
                <ModelSelect
                  value={form.default_chat_model}
                  onChange={(value) => update("default_chat_model", value)}
                  options={models.data?.chat ?? []}
                  placeholder="Pick a chat model"
                />
              </Field>

              <Field
                label="Default embedding model"
                hint="Pre-filled when creating a knowledge base."
              >
                <ModelSelect
                  value={form.default_embedding_model}
                  onChange={(value) => update("default_embedding_model", value)}
                  options={models.data?.embedding ?? []}
                  placeholder="Pick an embedding model"
                />
              </Field>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Chunks per answer" hint="How many passages feed the model.">
                <input
                  type="number"
                  min={1}
                  max={20}
                  className={inputClass}
                  value={form.top_k}
                  onChange={(event) => update("top_k", Number(event.target.value))}
                />
              </Field>

              <Field label="Temperature" hint="0 is focused, 1 is chatty.">
                <input
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  className={inputClass}
                  value={form.temperature}
                  onChange={(event) => update("temperature", Number(event.target.value))}
                />
              </Field>

              <Field label="Context window" hint="Tokens the model can see at once.">
                <select
                  className={inputClass}
                  value={form.num_ctx}
                  onChange={(event) => update("num_ctx", Number(event.target.value))}
                >
                  {CONTEXT_SIZES.map((size) => (
                    <option key={size} value={size}>
                      {size.toLocaleString()}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            <div className="flex items-center gap-3">
              <Button type="submit" variant="primary" disabled={save.isPending}>
                {save.isPending ? <Spinner /> : null}
                Save defaults
              </Button>
              {saved ? <span className="text-sm text-emerald-300">Saved</span> : null}
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
