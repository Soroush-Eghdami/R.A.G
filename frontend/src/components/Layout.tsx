import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { cx } from "../lib/format";
import { useHealth } from "../lib/hooks";
import { applyTheme, readTheme } from "../lib/theme";
import { ChatIcon, LibraryIcon, MoonIcon, SlidersIcon, SparkIcon, SunIcon } from "./icons";
import { Button, Spinner } from "./ui";

function RuntimeStatus() {
  const { data, isPending, isError } = useHealth();

  if (isPending) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted">
        <Spinner /> Checking model servers…
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

  const chatOnline = data.chat.reachable;
  const embeddingOnline = data.embedding.reachable;
  return (
    <div className="space-y-1.5 text-xs">
      <p className="font-semibold tracking-wide text-ink">llama.cpp runtime</p>
      <span className={cx("inline-flex items-center gap-2", chatOnline ? "text-success" : "text-danger")}>
        <span className={cx("size-1.5 rounded-full", chatOnline ? "bg-success" : "bg-danger")} />
        Chat {chatOnline ? "ready" : "offline"}
      </span>
      <span className={cx("inline-flex items-center gap-2", embeddingOnline ? "text-success" : "text-danger")}>
        <span className={cx("size-1.5 rounded-full", embeddingOnline ? "bg-success" : "bg-danger")} />
        Embeddings {embeddingOnline ? "ready" : "offline"}
      </span>
    </div>
  );
}

const navItem = ({ isActive }: { isActive: boolean }) =>
  cx(
    "group flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition md:px-3",
    isActive
      ? "bg-primary/10 text-primary ring-1 ring-inset ring-primary/15"
      : "text-muted hover:bg-elevated/60 hover:text-ink",
  );

export default function Layout() {
  const [theme, setTheme] = useState(readTheme);

  return (
    <div className="min-h-full">
      <aside className="fixed inset-x-0 bottom-0 z-30 flex h-16 flex-row items-center justify-between border-t border-line bg-surface/95 px-3 backdrop-blur-xl md:inset-y-0 md:right-auto md:h-auto md:w-64 md:flex-col md:items-stretch md:justify-start md:gap-7 md:border-t-0 md:border-r md:bg-surface/90 md:px-4 md:py-5">
        <div className="hidden items-center gap-3 px-2 pt-1 md:flex">
          <span className="grid size-10 place-items-center rounded-2xl bg-primary text-on-primary shadow-lg shadow-primary/20">
            <SparkIcon className="size-5" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight text-ink">Local RAG</p>
            <p className="truncate text-[11px] text-muted">Your private knowledge space</p>
          </div>
        </div>

        <nav className="flex flex-1 items-center justify-around gap-1 md:flex-col md:items-stretch md:justify-start">
          <NavLink
            to="/chat"
            className={navItem}
            aria-label="Chat"
            title="Chat"
          >
            <ChatIcon className="size-[18px]" />
            <span className="hidden sm:inline">Chat</span>
          </NavLink>
          <NavLink
            to="/kb"
            className={navItem}
            aria-label="Knowledge bases"
            title="Knowledge bases"
          >
            <LibraryIcon className="size-[18px]" />
            <span className="hidden sm:inline">Knowledge bases</span>
          </NavLink>
          <NavLink
            to="/settings"
            className={navItem}
            aria-label="Settings"
            title="Settings"
          >
            <SlidersIcon className="size-[18px]" />
            <span className="hidden sm:inline">Settings</span>
          </NavLink>
        </nav>

        <div className="flex items-center justify-end md:mt-auto md:block md:space-y-3">
          <Button
            variant="ghost"
            className="size-10 shrink-0 px-0 md:w-full md:justify-start md:px-3"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            onClick={() => {
              const next = theme === "dark" ? "light" : "dark";
              setTheme(next);
              applyTheme(next);
            }}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            <span className="hidden md:inline">
              {theme === "dark" ? "Light appearance" : "Dark appearance"}
            </span>
          </Button>

          <div className="hidden rounded-2xl border border-line bg-app/60 p-3 md:block">
            <RuntimeStatus />
          </div>
        </div>
      </aside>

      <main className="mb-16 px-4 py-5 sm:px-6 md:mb-0 md:ml-64 md:px-8 md:py-7">
        <div className="mx-auto w-full max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
