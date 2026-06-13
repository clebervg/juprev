import { Bell, Search, Sun, Moon } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useTheme } from "@/contexts/ThemeContext";

const BREADCRUMBS: Record<string, string> = {
  "/": "Dashboard",
  "/clientes": "Clientes",
  "/processos": "Processos",
  "/prazos": "Prazos",
  "/documentos": "Documentos",
};

export function Header() {
  const { pathname } = useLocation();
  const { theme, toggle } = useTheme();
  const page = BREADCRUMBS[pathname] ?? "Página";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 px-6 backdrop-blur-md">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-400 dark:text-slate-500">Juprev</span>
        <span className="text-slate-300 dark:text-slate-600">/</span>
        <span className="font-medium text-slate-800 dark:text-slate-200">{page}</span>
      </div>

      {/* Ações */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <button
          className="flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-1.5 text-sm text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          aria-label="Buscar"
        >
          <Search size={14} aria-hidden="true" />
          <span className="hidden sm:inline">Buscar...</span>
          <kbd className="hidden sm:inline-flex items-center rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-1.5 py-0.5 text-xs text-slate-400 dark:text-slate-500">
            ⌘K
          </kbd>
        </button>

        {/* Toggle dark mode */}
        <button
          onClick={toggle}
          className="rounded-lg p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          aria-label={theme === "dark" ? "Ativar modo claro" : "Ativar modo escuro"}
        >
          {theme === "dark" ? <Sun size={17} aria-hidden="true" /> : <Moon size={17} aria-hidden="true" />}
        </button>

        {/* Notificações */}
        <button
          className="relative rounded-lg p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          aria-label="Notificações"
        >
          <Bell size={17} aria-hidden="true" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-rose-500" aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
