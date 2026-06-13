import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FilePlus, Eye, Trash2, FileSearch, Clock } from "lucide-react";
import { toast } from "sonner";
import { cnisService } from "@/services/cnis";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SkeletonTable } from "@/components/ui/Skeleton";
import type { CNISListItem, StatusProcessamento } from "@/types/cnis";

const STATUS_LABEL: Record<StatusProcessamento, { label: string; className: string }> = {
  pendente:    { label: "Pendente",    className: "bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300" },
  processando: { label: "Processando", className: "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" },
  concluido:   { label: "Concluído",   className: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300" },
  erro:        { label: "Erro",        className: "bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300" },
};

function fmt(d: string | null) {
  if (!d) return "—";
  const [y, m] = d.split("-");
  return `${m}/${y}`;
}

export function CNISPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["cnis"],
    queryFn: () => cnisService.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: cnisService.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cnis"] });
      toast.success("CNIS excluído.");
    },
    onError: () => toast.error("Erro ao excluir CNIS."),
  });

  const handleDelete = (item: CNISListItem) => {
    if (!confirm(`Excluir o CNIS importado em ${new Date(item.created_at).toLocaleDateString("pt-BR")}? Esta ação não pode ser desfeita.`)) return;
    deleteMutation.mutate(item.id);
  };

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              CNIS / Cálculos Previdenciários
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {data ? `${data.total} registro${data.total !== 1 ? "s" : ""}` : "Carregando..."}
            </p>
          </div>
          <Button onClick={() => navigate("/cnis/novo")}>
            <FilePlus size={15} />
            Importar CNIS
          </Button>
        </div>

        {isLoading ? (
          <SkeletonTable rows={5} />
        ) : data?.items.length === 0 ? (
          <Card className="py-20 flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-slate-50 dark:bg-slate-700 mb-4">
              <FileSearch size={24} className="text-slate-300 dark:text-slate-500" />
            </div>
            <p className="font-medium text-slate-600 dark:text-slate-300">Nenhum CNIS importado</p>
            <p className="mt-1 text-sm text-slate-400">
              Importe o extrato CNIS de um cliente para iniciar os cálculos.
            </p>
            <Button className="mt-4" onClick={() => navigate("/cnis/novo")}>
              <FilePlus size={14} /> Importar CNIS
            </Button>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm" aria-label="Lista de CNIS">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
                    {["NIS", "Período", "Tempo Contrib.", "Contribuições", "Status", "Importado em", ""].map((h) => (
                      <th key={h} className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {data?.items.map((item: CNISListItem) => {
                    const st = STATUS_LABEL[item.status_processamento];
                    return (
                      <motion.tr
                        key={item.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="group hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                      >
                        <td className="px-6 py-4 font-mono text-xs text-slate-700 dark:text-slate-300">
                          {item.nis}
                        </td>
                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400 text-xs">
                          {fmt(item.periodo_inicial_cn)} → {fmt(item.periodo_final_cn)}
                        </td>
                        <td className="px-6 py-4 text-slate-600 dark:text-slate-300">
                          {item.tempo_contribuicao_anos != null
                            ? `${Number(item.tempo_contribuicao_anos).toFixed(1)} anos`
                            : "—"}
                        </td>
                        <td className="px-6 py-4 text-slate-500 dark:text-slate-400">
                          {item.total_contribuicoes ?? "—"}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${st.className}`}>
                            {item.status_processamento === "processando" && (
                              <Clock size={10} className="animate-spin" />
                            )}
                            {st.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-400 text-xs">
                          {new Date(item.created_at).toLocaleDateString("pt-BR")}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => navigate(`/cnis/${item.id}`)}
                              className="rounded-md p-1.5 text-slate-400 hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-950 transition-colors"
                              aria-label="Ver detalhes"
                            >
                              <Eye size={15} />
                            </button>
                            <button
                              onClick={() => handleDelete(item)}
                              className="rounded-md p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950 transition-colors"
                              aria-label="Excluir"
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </PageTransition>
  );
}
