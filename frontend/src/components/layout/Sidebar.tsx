import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  Scale,
  CalendarClock,
  FileText,
  LogOut,
  ChevronRight,
  ClipboardList,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/utils/cn";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/clientes", label: "Clientes", icon: Users },
  { to: "/cnis", label: "CNIS / Cálculos", icon: ClipboardList },
  { to: "/processos", label: "Processos", icon: FolderOpen },
  { to: "/prazos", label: "Prazos", icon: CalendarClock },
  { to: "/documentos", label: "Documentos", icon: FileText },
];

function getInitials(name: string): string {
  return name.split(" ").slice(0, 2).map((n) => n[0]).join("").toUpperCase();
}

const sidebarVariants = {
  hidden: { x: -280, opacity: 0 },
  show: { x: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 300, damping: 30 } },
};

const navItemVariants = {
  hidden: { opacity: 0, x: -12 },
  show: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.05 + 0.1, duration: 0.25 },
  }),
};

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <motion.aside
      variants={sidebarVariants}
      initial="hidden"
      animate="show"
      className="flex h-screen flex-col bg-slate-900"
      style={{ width: "280px", minWidth: "280px" }}
      aria-label="Navegação principal"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 shadow-indigo-glow">
          <Scale size={18} className="text-white" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-bold text-white tracking-tight">Juprev</p>
          <p className="text-xs text-slate-500">Sistema Previdenciário</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Menu
        </p>
        {NAV_ITEMS.map(({ to, label, icon: Icon }, i) => (
          <motion.div key={to} custom={i} variants={navItemVariants} initial="hidden" animate="show">
            <NavLink
              to={to}
              end
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-indigo-600 text-white shadow-indigo-glow"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={17} aria-hidden="true" className="shrink-0" />
                  <span className="flex-1">{label}</span>
                  {isActive && <ChevronRight size={14} className="opacity-70" aria-hidden="true" />}
                </>
              )}
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* User footer */}
      <div className="border-t border-slate-800 p-3">
        <div className="flex items-center gap-3 rounded-lg bg-slate-800/50 px-3 py-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500 text-xs font-semibold text-white">
            {user?.full_name ? getInitials(user.full_name) : "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-slate-200">{user?.full_name || "—"}</p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="shrink-0 rounded-md p-1.5 text-slate-500 hover:bg-slate-700 hover:text-slate-300 transition-colors"
            aria-label="Sair do sistema"
          >
            <LogOut size={15} aria-hidden="true" />
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
