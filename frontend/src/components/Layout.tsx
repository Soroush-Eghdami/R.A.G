import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { cx } from "../lib/format";
import { useHealth } from "../lib/hooks";
import { applyTheme, readTheme } from "../lib/theme";
import {
  ChatIcon,
  DatabaseIcon,
  LibraryIcon,
  MoonIcon,
  PanelIcon,
  SlidersIcon,
  SunIcon,
} from "./icons";
import { Button, Spinner } from "./ui";

const links = [
  { to: "/chat", label: "Ask your library", icon: ChatIcon },
  { to: "/kb", label: "Knowledge bases", icon: LibraryIcon },
  { to: "/settings", label: "Settings", icon: SlidersIcon },
];

function RuntimeStatus() {
  const { data, isPending, isError } = useHealth();

  if (isPending) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted">
        <Spinner /> Checking local models
      </div>
    );
  }

  const chatReady = !isError && Boolean(data?.chat.reachable);
  const embeddingReady = !isError && Boolean(data?.embedding.reachable);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-ink">Local models</span>
        <span
          className={cx(
            "size-2 rounded-full",
            chatReady && embeddingReady ? "bg-success" : "bg-warning",
          )}
          aria-label={chatReady && embeddingReady ? "Models online" : "Models offline"}
        />
      </div>
      <div className="space-y-1.5 text-[11px] text-muted">
        <p className="flex items-center justify-between gap-2">
          Chat <span className={chatReady ? "text-success" : "text-warning"}>{chatReady ? "Ready" : "Offline"}</span>
        </p>
        <p className="flex items-center justify-between gap-2">
          Embeddings{" "}
          <span className={embeddingReady ? "text-success" : "text-warning"}>
            {embeddingReady ? "Ready" : "Offline"}
          </span>
        </p>
      </div>
    </div>
  );
}

function navItem({ isActive }: { isActive: boolean }) {
  return cx(
    "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-colors",
    isActive
      ? "bg-primary-soft text-primary"
      : "text-ink-soft hover:bg-elevated hover:text-ink",
  );
}

export default function Layout() {
  const [theme, setTheme] = useState(readTheme);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
  }

  return (
    <div className="min-h-full md:flex">
      <aside
        id="app-sidebar"
        className={cx(
          "app-sidebar fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-line py-5 transition-[width] duration-200 md:flex",
          sidebarCollapsed ? "w-[72px] px-2.5" : "w-[248px] px-3.5",
        )}
      >
        <Button
          variant="ghost"
          className="absolute right-0 top-5 z-40 size-10 translate-x-1/2 rounded-full border border-line bg-surface p-0 text-ink-soft shadow-sm hover:text-ink"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-controls="app-sidebar"
          aria-expanded={!sidebarCollapsed}
          title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
        >
          <PanelIcon className={cx("size-5 transition-transform", sidebarCollapsed && "rotate-180")} />
        </Button>

        <NavLink
          to="/chat"
          aria-label="Local RAG"
          title={sidebarCollapsed ? "Local RAG" : undefined}
          className={cx(
            "mb-9 flex items-center gap-3 px-2",
            sidebarCollapsed && "justify-center px-0",
          )}
        >
          <span className="grid size-10 place-items-center rounded-[14px] bg-primary text-on-primary shadow-sm">
            <DatabaseIcon className="size-[19px]" />
          </span>
          {!sidebarCollapsed && (
            <span className="min-w-0">
              <span className="block text-[15px] font-semibold tracking-tight text-ink">Local RAG</span>
              <span className="mt-0.5 block text-[11px] text-muted">Your research workspace</span>
            </span>
          )}
        </NavLink>

        {!sidebarCollapsed && (
          <p className="mb-2 px-3 text-[10px] font-semibold tracking-[0.14em] text-muted uppercase">
            Workspace
          </p>
        )}
        <nav className="space-y-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              aria-label={label}
              title={sidebarCollapsed ? label : undefined}
              className={({ isActive }) =>
                cx(
                  navItem({ isActive }),
                  "w-full",
                  sidebarCollapsed && "h-11 justify-center gap-0 px-0",
                )
              }
            >
              <Icon className="size-[17px] opacity-80 transition group-hover:opacity-100" />
              {!sidebarCollapsed && label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-3">
          {!sidebarCollapsed && (
            <div className="rounded-2xl border border-line bg-surface/75 p-3.5">
              <RuntimeStatus />
            </div>
          )}
          <Button
            variant="ghost"
            className={cx(
              "w-full rounded-xl px-3 text-ink-soft",
              sidebarCollapsed ? "justify-center px-0" : "justify-start",
            )}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            title={sidebarCollapsed ? (theme === "dark" ? "Light appearance" : "Dark appearance") : undefined}
            onClick={toggleTheme}
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            {!sidebarCollapsed && (
              <span>{theme === "dark" ? "Light appearance" : "Dark appearance"}</span>
            )}
          </Button>
          {!sidebarCollapsed && (
            <p className="px-3 text-[10px] leading-relaxed text-muted">
              Private by design. Your documents stay on this device.
            </p>
          )}
        </div>
      </aside>

      <header className="app-sidebar fixed inset-x-0 top-0 z-20 flex h-14 items-center justify-between border-b border-line px-4 md:hidden">
        <NavLink to="/chat" className="flex items-center gap-2.5">
          <span className="grid size-8 place-items-center rounded-xl bg-primary text-on-primary">
            <DatabaseIcon className="size-4" />
          </span>
          <span className="text-sm font-semibold text-ink">Local RAG</span>
        </NavLink>
        <Button
          variant="ghost"
          className="size-9 px-0"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          onClick={toggleTheme}
        >
          {theme === "dark" ? <SunIcon /> : <MoonIcon />}
        </Button>
      </header>

      <nav className="app-sidebar fixed inset-x-0 bottom-0 z-30 flex h-[68px] items-center justify-around border-t border-line px-2 md:hidden">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cx(
                "flex min-w-[92px] flex-col items-center gap-1 rounded-xl py-1.5 text-[10px] font-medium transition",
                isActive ? "text-primary" : "text-muted",
              )
            }
          >
            <Icon className="size-[18px]" />
            {label === "Ask your library" ? "Ask" : label}
          </NavLink>
        ))}
      </nav>

      <main
        className={cx(
          "min-h-dvh min-w-0 flex-1 pb-[80px] pt-[68px] transition-[margin] duration-200 md:px-4 md:py-4",
          sidebarCollapsed ? "md:ml-[72px]" : "md:ml-[248px]",
        )}
      >
        <Outlet />
      </main>
    </div>
  );
}
