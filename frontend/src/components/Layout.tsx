import { NavLink, Outlet } from "react-router-dom";
import { useHealth } from "../lib/hooks";
import { cx } from "../lib/format";
import { Badge, Spinner } from "./ui";

function OllamaStatus() {
  const { data, isPending, isError } = useHealth();

  if (isPending) {
    return (
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <Spinner /> Checking Ollama…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="space-y-1 text-xs">
        <Badge tone="bad">Backend offline</Badge>
        <p className="text-slate-500">Could not reach /api/health.</p>
      </div>
    );
  }

  const online = data.ollama.reachable;
  return (
    <div className="space-y-1.5 text-xs">
      <Badge tone={online ? "ok" : "bad"}>
        <span
          className={cx(
            "size-1.5 rounded-full",
            online ? "bg-emerald-400" : "bg-red-400",
          )}
        />
        {online ? "Ollama online" : "Ollama offline"}
      </Badge>
      <p className="break-all text-slate-500">{data.ollama.base_url}</p>
      {data.ollama.version ? (
        <p className="text-slate-600">v{data.ollama.version}</p>
      ) : null}
    </div>
  );
}

const navItem = ({ isActive }: { isActive: boolean }) =>
  cx(
    "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition",
    isActive
      ? "bg-slate-800 text-white"
      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200",
  );

export default function Layout() {
  return (
    <div className="flex min-h-full">
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col border-r border-slate-800 bg-slate-900/40 p-4">
        <div className="mb-6 px-2">
          <p className="text-sm font-semibold tracking-wide text-white">Local RAG</p>
          <p className="text-xs text-slate-500">Ollama, nothing leaves this box</p>
        </div>

        <nav className="flex flex-col gap-1">
          <NavLink to="/kb" className={navItem}>
            Knowledge bases
          </NavLink>
          <NavLink to="/settings" className={navItem}>
            Settings
          </NavLink>
        </nav>

        <div className="mt-auto border-t border-slate-800 p-2 pt-4">
          <OllamaStatus />
        </div>
      </aside>

      <main className="ml-60 flex-1 px-8 py-8">
        <div className="mx-auto max-w-5xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
