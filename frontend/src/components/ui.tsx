import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "../lib/format";

type Variant = "primary" | "subtle" | "danger" | "ghost";

const variants: Record<Variant, string> = {
  primary:
    "bg-indigo-500 text-white hover:bg-indigo-400 disabled:bg-indigo-500/40 disabled:text-white/60",
  subtle:
    "bg-slate-800 text-slate-100 hover:bg-slate-700 disabled:text-slate-500",
  danger:
    "bg-red-500/15 text-red-300 ring-1 ring-inset ring-red-500/30 hover:bg-red-500/25",
  ghost: "text-slate-300 hover:bg-slate-800/70 hover:text-white",
};

export function Button({
  variant = "subtle",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={cx(
        "inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition disabled:cursor-not-allowed",
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
        "rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm",
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
  neutral: "bg-slate-800 text-slate-300 ring-slate-700",
  ok: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  warn: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  bad: "bg-red-500/15 text-red-300 ring-red-500/30",
  info: "bg-indigo-500/15 text-indigo-300 ring-indigo-500/30",
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
    bad: "border-red-500/30 bg-red-500/10 text-red-200",
    warn: "border-amber-500/30 bg-amber-500/10 text-amber-200",
    ok: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  };
  return (
    <div className={cx("rounded-lg border px-4 py-3 text-sm", styles[tone])}>
      {children}
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-800 px-6 py-16 text-center">
      <p className="text-base font-medium text-slate-200">{title}</p>
      {hint ? <p className="max-w-md text-sm text-slate-400">{hint}</p> : null}
      {action}
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
      <span className="text-sm font-medium text-slate-300">{label}</span>
      {children}
      {hint ? <span className="text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-slate-700 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20";
