import type { Source } from "../api/types";
import { cx } from "../lib/format";
import { CloseIcon } from "./icons";
import { Button } from "./ui";

type Props = {
  sources: Source[];
  active: number | null;
  onSelect: (n: number) => void;
  onClose: () => void;
};

export default function SourceDrawer({ sources, active, onSelect, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        type="button"
        aria-label="Close sources"
        className="flex-1 cursor-default bg-black/40 backdrop-blur-[1px]"
        onClick={onClose}
      />

      <aside className="animate-slide-in flex h-full w-full max-w-md flex-col border-l border-line bg-surface shadow-2xl">
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <div>
            <p className="text-sm font-semibold text-ink">Sources</p>
            <p className="text-xs text-muted">
              {sources.length} passage{sources.length === 1 ? "" : "s"} used
            </p>
          </div>
          <Button variant="ghost" onClick={onClose} aria-label="Close" className="px-2">
            <CloseIcon />
          </Button>
        </header>

        <div className="flex-1 space-y-2.5 overflow-y-auto p-4">
          {sources.length === 0 ? (
            <p className="px-1 py-6 text-sm text-muted">
              This answer did not use any passages.
            </p>
          ) : null}

          {sources.map((source) => {
            const isActive = active === source.n;
            return (
              <button
                key={source.n}
                type="button"
                onClick={() => onSelect(source.n)}
                className={cx(
                  "block w-full cursor-pointer rounded-xl border p-3.5 text-left transition",
                  isActive
                    ? "border-accent/50 bg-accent/5"
                    : "border-line bg-elevated/40 hover:border-primary/40 hover:bg-elevated",
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="grid size-6 shrink-0 place-items-center rounded-md bg-accent/12 text-xs font-semibold text-accent ring-1 ring-inset ring-accent/25">
                    {source.n}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">
                    {source.document || "source"}
                  </span>
                  {source.page !== null ? (
                    <span className="shrink-0 text-xs text-muted">p.{source.page}</span>
                  ) : null}
                </div>

                <p className="mt-2 line-clamp-5 text-xs leading-relaxed whitespace-pre-wrap text-muted">
                  {source.snippet}
                </p>

                <div className="mt-2.5 flex items-center gap-2">
                  <div className="h-1 w-16 overflow-hidden rounded-full bg-line">
                    <div
                      className="h-full rounded-full bg-accent/70"
                      style={{ width: `${Math.round((1 - source.distance) * 100)}%` }}
                    />
                  </div>
                  <span className="text-[11px] text-muted">
                    match {(1 - source.distance).toFixed(2)}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        <footer className="border-t border-line px-5 py-3 text-xs text-muted">
          Snippets are the first 300 characters of each passage.
        </footer>
      </aside>
    </div>
  );
}
