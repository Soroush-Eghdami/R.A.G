import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { cx } from "../lib/format";
import { useHealth } from "../lib/hooks";
import { applyTheme, readTheme } from "../lib/theme";
import { ChatIcon, LibraryIcon, MoonIcon, SlidersIcon, SparkIcon, SunIcon } from "./icons";
import { Button, Spinner } from "./ui";

function OllamaStatus() {
  const { data, isPending, isError } = useHealth();

  if (isPending) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted">
        <Spinner /> Checking Ollama…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="space-y-1 text-xs">
        <span className="inline-flex items-center gap-2 text-danger">
          <span className="size-2 rounded-full bg-danger" />
          Backend offline
        </span>
        <p className="text-muted">Could not reach /api/health.</p>
      </div>
    );
  }

  const online = data.ollama.reachable;
  return (
    <div className="space-y-1.5 text-xs">
      <span
        className={cx(
          "inline-flex items-center gap-2 font-medium",
          online ? "text-success" : "text-danger",
        )}
      >
        <span
          className={cx(
            "size-2 rounded-full",
            online ? "bg-success shadow-[0_0_0_3px] shadow-success/15" : "bg-danger",
          )}
        />
        Ollama {online ? "online" : "offline"}
      </span>
      <p className="truncate text-muted" title={data.ollama.base_url}>
        {data.ollama.base_url}
      </p>
      {data.ollama.version ? <p className="text-muted/70">v{data.ollama.version}</p> : null}
    </div>
  );
}

const navItem = ({ isActive }: { isActive: boolean }) =>
  cx(
    "group flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm font-medium transition",
    isActive
      ? "bg-elevated text-ink shadow-sm"
      : "text-muted hover:bg-elevated/60 hover:text-ink",
  );

export default function Layout() {
  const [theme, setTheme] = useState(readTheme);

  return (
    <div className="flex min-h-full bg-app">
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col gap-6 border-r border-line bg-surface px-3 py-4">
        <div className="flex items-center gap-2.5 px-2 pt-1">
          <span className="grid size-9 place-items-center rounded-xl bg-primary text-white shadow-sm shadow-primary/30">
            <SparkIcon className="size-5" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight text-ink">Local RAG</p>
            <p className="truncate text-[11px] text-muted">Private, on your machine</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1">
          <NavLink to="/chat" className={navItem}>
            {({ isActive }) => (
              <>
                <ChatIcon className={cx("size-[18px]", isActive && "text-accent")} />
                Chat
              </>
            )}
          </NavLink>
          <NavLink to="/kb" className={navItem}>
            {({ isActive }) => (
              <>
                <LibraryIcon className={cx("size-[18px]", isActive && "text-accent")} />
                Knowledge bases
              </>
            )}
          </NavLink>
          <NavLink to="/settings" className={navItem}>
            {({ isActive }) => (
              <>
                <SlidersIcon className={cx("size-[18px]", isActive && "text-accent")} />
                Settings
              </>
            )}
          </NavLink>
        </nav>

        <div className="mt-auto space-y-2">
          <Button
            variant="ghost"
            className="w-full justify-start px-3"
            onClick={() => {
              const next = theme === "dark" ? "light" : "dark";
              setTheme(next);
              applyTheme(next);
            }}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </Button>

          <div className="rounded-xl border border-line bg-app/60 p-3">
            <OllamaStatus />
          </div>
        </div>
      </aside>

      <main className="ml-60 flex-1 px-8 py-7">
        <div className="mx-auto w-full max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
