import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "../lib/format";

type Variant = "primary" | "subtle" | "danger" | "ghost";

const variants: Record<Variant, string> = {
  primary:
    "bg-gradient-to-br from-primary to-primary-hover text-on-primary shadow-md shadow-primary/15 hover:brightness-105 disabled:from-primary/50 disabled:to-primary/50 disabled:shadow-none",
  subtle: "bg-elevated text-ink hover:bg-line disabled:text-muted",
  danger:
    "bg-danger/10 text-danger ring-1 ring-inset ring-danger/25 hover:bg-danger/15 disabled:opacity-50",
  ghost: "text-muted hover:bg-elevated hover:text-ink",
};

export function Button({
  variant = "subtle",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={cx(
        "inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
        "disabled:cursor-not-allowed",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cx(
        "rounded-2xl border border-line bg-surface/90 p-5 shadow-[0_8px_30px_-20px_rgb(0_0_0_/_0.3)] backdrop-blur-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cx(
        "inline-block size-3.5 animate-spin rounded-full border-2 border-current border-t-transparent",
        className,
      )}
      aria-hidden="true"
    />
  );
}

type Tone = "neutral" | "ok" | "warn" | "bad" | "info";

const tones: Record<Tone, string> = {
  neutral: "bg-elevated text-muted ring-line",
  ok: "bg-success/10 text-success ring-success/25",
  warn: "bg-warning/10 text-warning ring-warning/25",
  bad: "bg-danger/10 text-danger ring-danger/25",
  info: "bg-accent/10 text-accent ring-accent/25",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Banner({
  tone = "bad",
  children,
}: {
  tone?: "bad" | "warn" | "ok";
  children: ReactNode;
}) {
  const styles = {
    bad: "border-danger/25 bg-danger/10 text-danger",
    warn: "border-warning/25 bg-warning/10 text-warning",
    ok: "border-success/25 bg-success/10 text-success",
  };
  return (
    <div className={cx("rounded-xl border px-4 py-3 text-sm", styles[tone])}>
      {children}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  hint,
  action,
}: {
  icon?: ReactNode;
  title: string;
  hint?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line bg-surface/40 px-6 py-16 text-center">
      {icon ? (
        <div className="grid size-11 place-items-center rounded-xl bg-elevated text-muted">
          {icon}
        </div>
      ) : null}
      <p className="text-base font-medium text-ink">{title}</p>
      {hint ? <p className="max-w-md text-sm text-muted">{hint}</p> : null}
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-medium text-ink">{label}</span>
      {children}
      {hint ? <span className="text-xs text-muted">{hint}</span> : null}
    </label>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
      </div>
      {actions}
    </header>
  );
}

export const inputClass =
  "w-full rounded-xl border border-line bg-elevated px-3 py-2 text-sm text-ink outline-none transition placeholder:text-muted/70 focus:border-primary/60 focus:ring-2 focus:ring-primary/20 disabled:opacity-60";
