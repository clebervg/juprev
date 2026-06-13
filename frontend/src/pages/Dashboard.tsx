import { motion } from "framer-motion";
import {
  Users,
  FolderOpen,
  CalendarClock,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Clock,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageTransition } from "@/components/ui/PageTransition";
import { useAuth } from "@/contexts/AuthContext";

const STATS = [
  {
    label: "Clientes ativos",
    value: "—",
    trend: null,
    icon: Users,
    iconBg: "bg-indigo-50 dark:bg-indigo-950",
    iconColor: "text-indigo-600 dark:text-indigo-400",
  },
  {
    label: "Processos em andamento",
    value: "—",
    trend: null,
    icon: FolderOpen,
    iconBg: "bg-violet-50 dark:bg-violet-950",
    iconColor: "text-violet-600 dark:text-violet-400",
  },
  {
    label: "Prazos esta semana",
    value: "—",
    trend: null,
    icon: CalendarClock,
    iconBg: "bg-amber-50 dark:bg-amber-950",
    iconColor: "text-amber-600 dark:text-amber-400",
  },
];

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export function Dashboard() {
  const { user } = useAuth();

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bom dia" : hour < 18 ? "Boa tarde" : "Boa noite";
  const firstName = user?.full_name?.split(" ")[0] ?? "Usuário";

  return (
    <PageTransition>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">

        {/* Page header */}
        <motion.div variants={item}>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {greeting}, {firstName} 👋
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Aqui está o resumo do escritório hoje.
          </p>
        </motion.div>

        {/* Stats cards */}
        <motion.div variants={item} className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {STATS.map(({ label, value, trend, icon: Icon, iconBg, iconColor }) => (
            <motion.div
              key={label}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
            >
              <Card className="p-6 cursor-default h-full">
                <div className="flex items-start justify-between">
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconBg}`}>
                    <Icon size={17} className={iconColor} aria-hidden="true" />
                  </div>
                </div>
                <p className="mt-4 text-3xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
                {trend !== null && (
                  <div className="mt-2 flex items-center gap-1 text-xs">
                    {(trend as number) >= 0 ? (
                      <>
                        <TrendingUp size={13} className="text-emerald-500" />
                        <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                          {trend}% este mês
                        </span>
                      </>
                    ) : (
                      <>
                        <TrendingDown size={13} className="text-rose-500" />
                        <span className="text-rose-600 dark:text-rose-400 font-medium">
                          {Math.abs(trend as number)}% este mês
                        </span>
                      </>
                    )}
                  </div>
                )}
                <div className="mt-4 h-1 w-full rounded-full bg-slate-100 dark:bg-slate-700">
                  <div className="h-1 w-0 rounded-full bg-indigo-200 dark:bg-indigo-800" />
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Content grid */}
        <motion.div variants={item} className="grid grid-cols-1 gap-5 lg:grid-cols-3">

          {/* Atividade recente */}
          <Card className="lg:col-span-2">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 px-6 py-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  Atividade recente
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">Últimas ações no sistema</p>
              </div>
              <Button variant="ghost" size="sm">
                Ver tudo <ArrowRight size={13} />
              </Button>
            </div>
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-50 dark:bg-slate-700 mb-3">
                <Clock size={22} className="text-slate-300 dark:text-slate-500" />
              </div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                Nenhuma atividade ainda
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                As ações do sistema aparecerão aqui.
              </p>
            </div>
          </Card>

          {/* Prazos próximos */}
          <Card>
            <div className="border-b border-slate-100 dark:border-slate-700 px-6 py-4">
              <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Prazos próximos
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">Próximos 7 dias</p>
            </div>
            <div className="flex flex-col items-center justify-center py-16 text-center px-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 dark:bg-amber-950 mb-3">
                <CalendarClock size={22} className="text-amber-400" />
              </div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                Sem prazos próximos
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                Prazos dos processos aparecerão aqui.
              </p>
            </div>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <p className="text-xs text-slate-300 dark:text-slate-600">tenant · {user?.tenant_id}</p>
        </motion.div>

      </motion.div>
    </PageTransition>
  );
}
