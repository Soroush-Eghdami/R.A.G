import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ApiError, getSettings, updateSettings } from "../api/client";
import type { AppSettings } from "../api/types";
import { useHealth, useModels } from "../lib/hooks";
import { cx } from "../lib/format";
import { DatabaseIcon, SlidersIcon } from "../components/icons";
import {
  Badge,
  Banner,
  Button,
  Card,
  Field,
  PageHeader,
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
    <select
      className={inputClass}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
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

function SectionHead({
  icon,
  title,
  hint,
  action,
}: {
  icon: ReactNode;
  title: string;
  hint: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
          {icon}
        </span>
        <div>
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          <p className="text-sm text-muted">{hint}</p>
        </div>
      </div>
      {action}
    </div>
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
  const dbOk = health.data?.database.ok ?? false;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Connection status and the defaults new chats start from."
      />

      <Card className="space-y-4">
        <SectionHead
          icon={<DatabaseIcon className="size-[18px]" />}
          title="Ollama"
          hint="The model server running on this machine."
          action={
            <Button
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ["health"] });
                queryClient.invalidateQueries({ queryKey: ["models"] });
              }}
            >
              Recheck
            </Button>
          }
        />

        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cx(
              "inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
              online
                ? "bg-success/10 text-success ring-success/25"
                : "bg-danger/10 text-danger ring-danger/25",
            )}
          >
            <span
              className={cx(
                "size-1.5 rounded-full",
                online ? "bg-success" : "bg-danger",
              )}
            />
            {online ? "reachable" : "offline"}
          </span>
          {health.data?.ollama.version ? (
            <Badge>v{health.data.ollama.version}</Badge>
          ) : null}
          <Badge tone={dbOk ? "ok" : "bad"}>database {dbOk ? "ok" : "down"}</Badge>
        </div>

        <p className="rounded-xl border border-line bg-app/50 px-3 py-2 font-mono text-xs break-all text-muted">
          {health.data?.ollama.base_url ?? "…"}
        </p>

        {!online && health.data?.ollama.error ? (
          <Banner tone="warn">{health.data.ollama.error}</Banner>
        ) : null}

        {models.data ? (
          <p className="text-xs text-muted">
            {models.data.chat.length} chat model{models.data.chat.length === 1 ? "" : "s"},{" "}
            {models.data.embedding.length} embedding model
            {models.data.embedding.length === 1 ? "" : "s"}
            {models.data.cloud_hidden > 0
              ? ` · ${models.data.cloud_hidden} cloud model(s) hidden`
              : ""}
          </p>
        ) : null}
      </Card>

      <Card className="space-y-5">
        <SectionHead
          icon={<SlidersIcon className="size-[18px]" />}
          title="Defaults"
          hint="Used when a conversation or knowledge base does not pick its own."
        />

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
          <div className="flex items-center gap-2 text-sm text-muted">
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

            <div className="flex items-center gap-3 border-t border-line pt-4">
              <Button type="submit" variant="primary" disabled={save.isPending}>
                {save.isPending ? <Spinner /> : null}
                Save defaults
              </Button>
              {saved ? <span className="text-sm font-medium text-success">Saved</span> : null}
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
