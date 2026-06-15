import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import {
  ArrowLeft, Calculator, CheckCircle2, XCircle, AlertTriangle, Info,
} from "lucide-react";
import { toast } from "sonner";
import { cnisService } from "@/services/cnis";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { TIPOS_BENEFICIO, type TipoBeneficio, type CalculoRMI } from "@/types/cnis";

const schema = z.object({
  nome_calculo: z.string().min(2, "Nome obrigatório"),
  tipo_beneficio: z.string().min(1, "Selecione o tipo"),
  data_der: z.string().min(1, "Data obrigatória"),
  genero: z.enum(["masculino", "feminino"]),
  data_nascimento: z.string().optional(),
  tempo_especial_dias: z.coerce.number().int().min(0).optional(),
  grau_deficiencia: z.enum(["leve", "moderada", "grave", ""]).optional(),
  regra_aplicada: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const BRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function ResultadoCalculo({ calculo }: { calculo: CalculoRMI }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* RMI Final em destaque */}
      <div className={`rounded-xl border-2 p-6 text-center ${
        calculo.calculo_valido
          ? "border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20"
          : "border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-900/20"
      }`}>
        <div className="flex justify-center mb-2">
          {calculo.calculo_valido
            ? <CheckCircle2 size={28} className="text-emerald-500" />
            : <XCircle size={28} className="text-rose-500" />}
        </div>
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Renda Mensal Inicial (RMI)</p>
        <p className="text-4xl font-bold text-slate-900 dark:text-slate-100 mt-1">
          {BRL(calculo.rmi_final)}
        </p>
        {calculo.rmi_calculada !== calculo.rmi_final && (
          <p className="text-xs text-slate-400 mt-1">
            RMI calculada: {BRL(calculo.rmi_calculada)} → limitada ao teto INSS ({BRL(calculo.rmi_teto ?? 0)})
          </p>
        )}
        <p className="text-xs text-slate-500 mt-1">{calculo.regra_aplicada}</p>
      </div>

      {/* Detalhes */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label: "Salário de Benefício", value: BRL(calculo.salario_beneficio) },
          { label: "Coeficiente", value: `${(calculo.coeficiente_calculo * 100).toFixed(2)}%` },
          { label: "Fator Previdenciário", value: calculo.fator_previdenciario?.toFixed(6) ?? "N/A" },
          { label: "Idade na DER", value: `${calculo.idade_na_der} anos` },
          { label: "TC na DER", value: `${Number(calculo.tempo_contribuicao_na_der).toFixed(1)} anos` },
          { label: "Salários analisados", value: calculo.detalhamento_calculo?.total_salarios_analisados?.toString() ?? "—" },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-3 text-center">
            <p className="text-xs text-slate-400 mb-0.5">{label}</p>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{value}</p>
          </div>
        ))}
      </div>

      {/* Requisitos */}
      {calculo.requisitos_atendidos && (
        <Card className="p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-3">Requisitos</p>
          <div className="space-y-1.5">
            {Object.entries(calculo.requisitos_atendidos).map(([k, v]) => {
              if (typeof v === "boolean") {
                return (
                  <div key={k} className="flex items-center gap-2 text-sm">
                    {v ? (
                      <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                    ) : (
                      <XCircle size={14} className="text-rose-500 shrink-0" />
                    )}
                    <span className="text-slate-600 dark:text-slate-400 capitalize">
                      {k.replace(/_/g, " ")}
                    </span>
                  </div>
                );
              }
              return (
                <div key={k} className="flex items-center justify-between text-xs text-slate-500">
                  <span className="capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="font-mono">{String(v)}</span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Passo a passo */}
      {calculo.detalhamento_calculo?.passo_a_passo?.length > 0 && (
        <Card className="p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-3">Passo a Passo do Cálculo</p>
          <ol className="space-y-1.5">
            {calculo.detalhamento_calculo.passo_a_passo.map((p, i) => (
              <li key={i} className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-700/50 rounded px-3 py-2">
                {p}
              </li>
            ))}
          </ol>
        </Card>
      )}

      {/* Alertas */}
      {calculo.alertas?.length ? (
        <div className="space-y-1.5">
          {calculo.alertas.map((a, i) => (
            <div key={i} className="flex gap-2 text-sm text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              {a}
            </div>
          ))}
        </div>
      ) : null}

      {/* Comparativo */}
      {calculo.rmi_regra_anterior && (
        <div className="flex items-start gap-2 text-sm text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg px-3 py-2">
          <Info size={14} className="shrink-0 mt-0.5" />
          <span>
            Pela regra anterior (fator previdenciário): {BRL(calculo.rmi_regra_anterior)}
            {calculo.diferenca_reforma != null && (
              <span className={calculo.diferenca_reforma >= 0 ? " text-emerald-600" : " text-rose-600"}>
                {" "}({calculo.diferenca_reforma >= 0 ? "+" : ""}{BRL(calculo.diferenca_reforma)} com a reforma)
              </span>
            )}
          </span>
        </div>
      )}
    </motion.div>
  );
}

export function CalculoRMIForm() {
  const { cnisId } = useParams<{ cnisId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [resultado, setResultado] = useState<CalculoRMI | null>(null);

  const { data: cnis } = useQuery({
    queryKey: ["cnis", cnisId],
    queryFn: () => cnisService.get(cnisId!),
    enabled: !!cnisId,
  });

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      genero: "masculino",
      tempo_especial_dias: 0,
    },
  });

  const tipoBeneficio = watch("tipo_beneficio") as TipoBeneficio | undefined;
  const isEspecial = tipoBeneficio?.startsWith("aposentadoria_especial");
  const isPcd = tipoBeneficio?.startsWith("aposentadoria_pcd");

  const calcularMutation = useMutation({
    mutationFn: async (data: FormData) => {
      const body = {
        cnis_id: cnisId!,
        tipo_beneficio: data.tipo_beneficio as TipoBeneficio,
        data_der: data.data_der,
        nome_calculo: data.nome_calculo,
        regra_aplicada: data.regra_aplicada || undefined,
      };
      const params = {
        genero: data.genero,
        data_nascimento: data.data_nascimento || undefined,
        tempo_especial_dias: data.tempo_especial_dias || 0,
        grau_deficiencia: data.grau_deficiencia || undefined,
      };
      return cnisService.calcular(cnisId!, body, params);
    },
    onSuccess: (data) => {
      setResultado(data);
      qc.invalidateQueries({ queryKey: ["cnis", cnisId, "calculos"] });
      toast.success("Cálculo executado com sucesso.");
    },
    onError: (e: { response?: { data?: { detail?: string } } }) => {
      const msg = e?.response?.data?.detail ?? "Erro ao executar cálculo.";
      toast.error(msg, { duration: 8000 });
    },
  });

  return (
    <PageTransition>
      <div className="space-y-6 max-w-3xl">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/cnis/${cnisId}`)}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Calcular RMI
            </h1>
            <p className="mt-1 text-sm text-slate-500 font-mono">{cnis?.nis}</p>
          </div>
        </div>

        <Card className="p-6">
          <form onSubmit={handleSubmit((d) => calcularMutation.mutate(d))} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Nome */}
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Nome do Cálculo
                </label>
                <input
                  {...register("nome_calculo")}
                  placeholder="Ex: Aposentadoria por Idade - Cenário Principal"
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
                {errors.nome_calculo && (
                  <p className="mt-1 text-xs text-rose-500">{errors.nome_calculo.message}</p>
                )}
              </div>

              {/* Tipo */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Tipo de Benefício
                </label>
                <select
                  {...register("tipo_beneficio")}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="">Selecione...</option>
                  {Object.entries(TIPOS_BENEFICIO).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
                {errors.tipo_beneficio && (
                  <p className="mt-1 text-xs text-rose-500">{errors.tipo_beneficio.message}</p>
                )}
              </div>

              {/* DER */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  DER — Data de Entrada do Requerimento
                </label>
                <input
                  type="date"
                  {...register("data_der")}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
                {errors.data_der && (
                  <p className="mt-1 text-xs text-rose-500">{errors.data_der.message}</p>
                )}
              </div>

              {/* Gênero */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
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

              {/* Data nascimento override */}
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Data de Nascimento <span className="text-slate-400 font-normal">(opcional — usa a do CNIS)</span>
                </label>
                <input
                  type="date"
                  {...register("data_nascimento")}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              {/* Tempo especial */}
              {isEspecial && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Tempo Especial (dias)
                  </label>
                  <input
                    type="number"
                    min={0}
                    {...register("tempo_especial_dias")}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              )}

              {/* Grau de deficiência */}
              {isPcd && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Grau de Deficiência
                  </label>
                  <select
                    {...register("grau_deficiencia")}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">Selecione...</option>
                    <option value="leve">Leve</option>
                    <option value="moderada">Moderada</option>
                    <option value="grave">Grave</option>
                  </select>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <Button type="submit" loading={calcularMutation.isPending} size="lg">
                <Calculator size={16} />
                Calcular RMI
              </Button>
            </div>
          </form>
        </Card>

        {resultado && <ResultadoCalculo calculo={resultado} />}
      </div>
    </PageTransition>
  );
}
