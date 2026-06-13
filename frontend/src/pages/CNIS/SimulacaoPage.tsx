import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { ArrowLeft, TrendingUp, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { cnisService } from "@/services/cnis";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { Simulacao } from "@/types/cnis";

const schema = z.object({
  nome_simulacao: z.string().optional(),
  data_simulacao_futura: z.string().min(1, "Data obrigatória"),
  taxa_crescimento_salario: z.coerce.number().min(0).max(100),
  taxa_inflacao_anual: z.coerce.number().min(0).max(100),
  genero: z.enum(["masculino", "feminino"]),
});

type FormData = z.infer<typeof schema>;

const BRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function SimulacaoCard({ sim, onDelete }: { sim: Simulacao; onDelete: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p className="font-semibold text-slate-800 dark:text-slate-200">
            {sim.nome_simulacao || `Simulação — ${sim.data_simulacao_futura}`}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            Aposentadoria em {new Date(sim.data_simulacao_futura + "T12:00").toLocaleDateString("pt-BR")}
          </p>
        </div>
        <button
          onClick={onDelete}
          className="rounded-md p-1.5 text-slate-300 hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-900/20 transition-colors"
        >
          <Trash2 size={13} />
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: "Idade", value: sim.idade_na_data ? `${sim.idade_na_data} anos` : "—" },
          { label: "TC projetado", value: sim.tempo_contribuicao_projetado ? `${Number(sim.tempo_contribuicao_projetado).toFixed(1)} anos` : "—" },
          { label: "RMI projetada", value: sim.rmi_projetada ? BRL(sim.rmi_projetada) : "—" },
          { label: "Valor atual", value: sim.rmi_valor_atual ? BRL(sim.rmi_valor_atual) : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-50 dark:bg-slate-700/50 rounded-lg px-3 py-2 text-center">
            <p className="text-xs text-slate-400 mb-0.5">{label}</p>
            <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function SimulacaoPage() {
  const { cnisId } = useParams<{ cnisId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: cnis } = useQuery({
    queryKey: ["cnis", cnisId],
    queryFn: () => cnisService.get(cnisId!),
    enabled: !!cnisId,
  });

  const { data: simulacoes = [] } = useQuery<Simulacao[]>({
    queryKey: ["cnis", cnisId, "simulacoes"],
    queryFn: async () => {
      // Endpoint de listagem de simulações ainda não exposto — usamos cache local
      return qc.getQueryData<Simulacao[]>(["cnis", cnisId, "simulacoes"]) ?? [];
    },
  });

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      taxa_crescimento_salario: 3,
      taxa_inflacao_anual: 4.5,
      genero: "masculino",
    },
  });

  const simularMutation = useMutation({
    mutationFn: (data: FormData) =>
      cnisService.simular(
        cnisId!,
        {
          cnis_id: cnisId!,
          nome_simulacao: data.nome_simulacao || undefined,
          data_simulacao_futura: data.data_simulacao_futura,
          taxa_crescimento_salario: data.taxa_crescimento_salario / 100,
          taxa_inflacao_anual: data.taxa_inflacao_anual / 100,
        },
        { genero: data.genero },
      ),
    onSuccess: (nova) => {
      qc.setQueryData<Simulacao[]>(["cnis", cnisId, "simulacoes"], (prev) => [
        ...(prev ?? []),
        nova,
      ]);
      toast.success("Simulação gerada.");
    },
    onError: () => toast.error("Erro ao simular."),
  });

  const handleDelete = (id: string) => {
    qc.setQueryData<Simulacao[]>(["cnis", cnisId, "simulacoes"], (prev) =>
      (prev ?? []).filter((s) => s.id !== id)
    );
  };

  // Dados para o gráfico — ordena por data
  const chartData = [...simulacoes]
    .sort((a, b) => a.data_simulacao_futura.localeCompare(b.data_simulacao_futura))
    .map((s) => ({
      data: s.data_simulacao_futura.slice(0, 7),
      "RMI Projetada": s.rmi_projetada ?? 0,
      "Valor Presente": s.rmi_valor_atual ?? 0,
    }));

  return (
    <PageTransition>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/cnis/${cnisId}`)}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Simulação de Cenários
            </h1>
            <p className="mt-1 text-sm text-slate-500 font-mono">{cnis?.nis}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Formulário */}
          <div className="lg:col-span-1">
            <Card className="p-5">
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4 flex items-center gap-2">
                <TrendingUp size={15} /> Nova Simulação
              </p>
              <form onSubmit={handleSubmit((d) => simularMutation.mutate(d))} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Nome (opcional)
                  </label>
                  <input
                    {...register("nome_simulacao")}
                    placeholder="Ex: Aposentadoria 2030"
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Data de Aposentadoria
                  </label>
                  <input
                    type="date"
                    {...register("data_simulacao_futura")}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                  {errors.data_simulacao_futura && (
                    <p className="mt-1 text-xs text-rose-500">{errors.data_simulacao_futura.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Gênero
                  </label>
                  <select
                    {...register("genero")}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="masculino">Masculino</option>
                    <option value="feminino">Feminino</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Crescimento salarial anual (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    {...register("taxa_crescimento_salario")}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Inflação anual (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    {...register("taxa_inflacao_anual")}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <Button type="submit" loading={simularMutation.isPending} className="w-full">
                  <TrendingUp size={14} />
                  Simular
                </Button>
              </form>
            </Card>
          </div>

          {/* Resultados + Gráfico */}
          <div className="lg:col-span-2 space-y-4">
            {simulacoes.length > 1 && (
              <Card className="p-5">
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">Comparativo de Cenários</p>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gradRMI" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gradVP" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="data" tick={{ fontSize: 11 }} />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) => `R$${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(v) => BRL(Number(v))}
                      contentStyle={{ fontSize: 12 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Area type="monotone" dataKey="RMI Projetada" stroke="#6366f1" fill="url(#gradRMI)" strokeWidth={2} />
                    <Area type="monotone" dataKey="Valor Presente" stroke="#10b981" fill="url(#gradVP)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            )}

            {simulacoes.length === 0 ? (
              <Card className="py-20 flex flex-col items-center text-center">
                <TrendingUp size={32} className="text-slate-300 mb-3" />
                <p className="font-medium text-slate-600 dark:text-slate-300">Nenhuma simulação ainda</p>
                <p className="text-sm text-slate-400 mt-1">Configure uma data e premissas para simular.</p>
              </Card>
            ) : (
              <div className="space-y-3">
                {simulacoes.map((s) => (
                  <SimulacaoCard key={s.id} sim={s} onDelete={() => handleDelete(s.id)} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
