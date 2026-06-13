import { useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Calculator, TrendingUp, AlertTriangle, CheckCircle2,
  XCircle, Calendar, ChevronDown, ChevronUp, Plus, Trash2, Upload,
  FileCheck2, X, DollarSign, Pencil,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { cnisService } from "@/services/cnis";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import type { CalculoRMI, RemuneracaoItem, TipoRemuneracao } from "@/types/cnis";
import { TIPOS_BENEFICIO, TIPOS_REMUNERACAO } from "@/types/cnis";

type Tab = "geral" | "calculos" | "inconsistencias" | "remuneracoes";

const BRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function SummaryCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
    </div>
  );
}

function CalculoCard({ calculo }: { calculo: CalculoRMI }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden">
      <div className="flex items-start justify-between gap-4 p-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-slate-800 dark:text-slate-200 truncate">{calculo.nome_calculo}</p>
            {calculo.calculo_valido ? (
              <CheckCircle2 size={15} className="text-emerald-500 shrink-0" />
            ) : (
              <XCircle size={15} className="text-rose-500 shrink-0" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {TIPOS_BENEFICIO[calculo.tipo_beneficio]} · DER: {calculo.data_der}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
            {BRL(calculo.rmi_final)}
          </p>
          <p className="text-xs text-slate-400">RMI final</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-slate-100 dark:bg-slate-700">
        {[
          { label: "Salário Benefício", value: BRL(calculo.salario_beneficio) },
          { label: "Coeficiente", value: `${(calculo.coeficiente_calculo * 100).toFixed(2)}%` },
          { label: "Fator Prev.", value: calculo.fator_previdenciario ? calculo.fator_previdenciario.toFixed(4) : "N/A" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-slate-50 dark:bg-slate-800/80 px-3 py-2 text-center">
            <p className="text-xs text-slate-400">{label}</p>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">{value}</p>
          </div>
        ))}
      </div>

      {(calculo.alertas?.length || calculo.erros?.length || calculo.detalhamento_calculo?.passo_a_passo?.length) && (
        <div className="border-t border-slate-100 dark:border-slate-700">
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-2.5 text-xs text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
          >
            <span>Ver detalhamento</span>
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="px-4 pb-4 space-y-3">
                  {calculo.detalhamento_calculo?.passo_a_passo?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Passo a Passo</p>
                      <ol className="space-y-1">
                        {calculo.detalhamento_calculo.passo_a_passo.map((p, i) => (
                          <li key={i} className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-700/50 rounded px-2.5 py-1.5">
                            {p}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                  {calculo.alertas?.length && (
                    <div>
                      <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1.5">Alertas</p>
                      {calculo.alertas.map((a, i) => (
                        <div key={i} className="flex gap-2 text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded px-2.5 py-1.5">
                          <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                          {a}
                        </div>
                      ))}
                    </div>
                  )}
                  {calculo.erros?.length && (
                    <div>
                      {calculo.erros.map((e, i) => (
                        <div key={i} className="flex gap-2 text-xs text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20 rounded px-2.5 py-1.5">
                          <XCircle size={12} className="shrink-0 mt-0.5" />
                          {e}
                        </div>
                      ))}
                    </div>
                  )}
                  {calculo.rmi_regra_anterior && (
                    <div className="text-xs bg-indigo-50 dark:bg-indigo-900/20 rounded px-2.5 py-1.5 text-indigo-700 dark:text-indigo-300">
                      Regra anterior: {BRL(calculo.rmi_regra_anterior)} · Diferença: {BRL(calculo.diferenca_reforma ?? 0)}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

const BRL_FMT = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

// ─── Schema para nova remuneração ────────────────────────────────────────────
const remSchema = z.object({
  competencia: z.string().regex(/^\d{2}\/\d{4}$/, "Use MM/AAAA"),
  salario_contribuicao: z.coerce.number().min(0, "Valor inválido"),
  tipo_remuneracao: z.string() as z.ZodType<TipoRemuneracao>,
  contribuiu_inss: z.boolean(),
});
type RemForm = z.infer<typeof remSchema>;

const inputCls =
  "w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20";

// ─── Modal editar remuneração ─────────────────────────────────────────────────
function ModalEditarRemuneracao({
  cnisId,
  remuneracao,
  onClose,
}: {
  cnisId: string;
  remuneracao: RemuneracaoItem;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RemForm>({
    resolver: zodResolver(remSchema),
    defaultValues: {
      competencia: `${String(remuneracao.mes).padStart(2, "0")}/${remuneracao.ano}`,
      salario_contribuicao: remuneracao.salario_contribuicao,
      tipo_remuneracao: (remuneracao.tipo_remuneracao as TipoRemuneracao) ?? "salario",
      contribuiu_inss: remuneracao.contribuiu_inss,
    },
  });

  const mutation = useMutation({
    mutationFn: (d: RemForm) => {
      const [mm, yyyy] = d.competencia.split("/");
      return cnisService.editarRemuneracao(cnisId, remuneracao.id, {
        competencia: `${yyyy}-${mm}-01`,
        salario_contribuicao: d.salario_contribuicao,
        tipo_remuneracao: d.tipo_remuneracao,
        contribuiu_inss: d.contribuiu_inss,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cnis", cnisId, "remuneracoes"] });
      qc.invalidateQueries({ queryKey: ["cnis", cnisId] });
      toast.success("Remuneração atualizada.");
      onClose();
    },
    onError: (e: { response?: { data?: { detail?: string } } }) => {
      toast.error(e?.response?.data?.detail ?? "Erro ao atualizar.");
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-800 shadow-xl p-6"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100">Editar Remuneração</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:text-slate-600 transition-colors">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Competência (MM/AAAA)</label>
            <input {...register("competencia")} placeholder="01/2020" className={inputCls} />
            {errors.competencia && <p className="mt-1 text-xs text-rose-500">{errors.competencia.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Salário de Contribuição (R$)</label>
            <input {...register("salario_contribuicao")} type="number" step="0.01" min="0" placeholder="0,00" className={inputCls} />
            {errors.salario_contribuicao && <p className="mt-1 text-xs text-rose-500">{errors.salario_contribuicao.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Tipo</label>
            <select {...register("tipo_remuneracao")} className={inputCls}>
              {(Object.entries(TIPOS_REMUNERACAO) as [TipoRemuneracao, string][]).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input {...register("contribuiu_inss")} type="checkbox" className="rounded" />
            <span className="text-sm text-slate-700 dark:text-slate-300">Contribuiu ao INSS</span>
          </label>
          <div className="flex justify-end gap-3 pt-1">
            <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button type="submit" loading={mutation.isPending}>Salvar</Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

// ─── Modal nova remuneração ───────────────────────────────────────────────────
function ModalNovaRemuneracao({
  cnisId,
  onClose,
}: {
  cnisId: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RemForm>({
    resolver: zodResolver(remSchema),
    defaultValues: { tipo_remuneracao: "salario", contribuiu_inss: true },
  });

  const mutation = useMutation({
    mutationFn: (d: RemForm) => {
      const [mm, yyyy] = d.competencia.split("/");
      return cnisService.criarRemuneracao(cnisId, {
        competencia: `${yyyy}-${mm}-01`,
        salario_contribuicao: d.salario_contribuicao,
        tipo_remuneracao: d.tipo_remuneracao,
        contribuiu_inss: d.contribuiu_inss,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cnis", cnisId, "remuneracoes"] });
      qc.invalidateQueries({ queryKey: ["cnis", cnisId] });
      toast.success("Remuneração cadastrada.");
      onClose();
    },
    onError: (e: { response?: { data?: { detail?: string } } }) => {
      const msg = e?.response?.data?.detail ?? "Erro ao cadastrar.";
      toast.error(msg);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-800 shadow-xl p-6"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100">Nova Remuneração</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:text-slate-600 transition-colors">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Competência (MM/AAAA)</label>
            <input {...register("competencia")} placeholder="01/2020" className={inputCls} />
            {errors.competencia && <p className="mt-1 text-xs text-rose-500">{errors.competencia.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Salário de Contribuição (R$)</label>
            <input {...register("salario_contribuicao")} type="number" step="0.01" min="0" placeholder="0,00" className={inputCls} />
            {errors.salario_contribuicao && <p className="mt-1 text-xs text-rose-500">{errors.salario_contribuicao.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Tipo</label>
            <select {...register("tipo_remuneracao")} className={inputCls}>
              {(Object.entries(TIPOS_REMUNERACAO) as [TipoRemuneracao, string][]).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input {...register("contribuiu_inss")} type="checkbox" className="rounded" />
            <span className="text-sm text-slate-700 dark:text-slate-300">Contribuiu ao INSS</span>
          </label>
          <div className="flex justify-end gap-3 pt-1">
            <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
            <Button type="submit" loading={mutation.isPending}>Cadastrar</Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

// ─── Modal importar CSV ───────────────────────────────────────────────────────
function ModalImportarCSV({
  cnisId,
  onClose,
}: {
  cnisId: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [preview, setPreview] = useState<{ competencia: string; salario: string }[]>([]);

  const parsePreview = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const linhas = text.split("\n");
      const rows: { competencia: string; salario: string }[] = [];
      linhas.forEach((linha, i) => {
        linha = linha.trim();
        if (!linha) return;
        const partes = linha.split(",");
        if (i === 0 && partes[0]?.toLowerCase().includes("compet")) return;
        if (partes.length >= 2) rows.push({ competencia: partes[0].trim(), salario: partes[1].trim() });
      });
      setPreview(rows.slice(0, 10));
    };
    reader.readAsText(file, "utf-8");
  };

  const mutation = useMutation({
    mutationFn: (f: File) => cnisService.importarCSV(cnisId, f),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["cnis", cnisId, "remuneracoes"] });
      qc.invalidateQueries({ queryKey: ["cnis", cnisId] });
      toast.success(`Importação concluída: ${res.criadas} criadas, ${res.ignoradas} duplicatas.`);
      if (res.erros.length) toast.warning(`${res.erros.length} linha(s) com erro.`);
      onClose();
    },
    onError: () => toast.error("Erro ao importar CSV."),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.96 }}
        className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-800 shadow-xl p-6"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100">Importar CSV</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:text-slate-600 transition-colors">
            <X size={16} />
          </button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          O arquivo deve ter duas colunas: <code className="bg-slate-100 dark:bg-slate-700 px-1 rounded">competencia</code> (MM/AAAA ou AAAA-MM) e <code className="bg-slate-100 dark:bg-slate-700 px-1 rounded">salario</code>.
        </p>

        {!arquivo ? (
          <div
            onClick={() => inputRef.current?.click()}
            className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-200 dark:border-slate-600 cursor-pointer px-6 py-10 text-center hover:border-indigo-300 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
          >
            <Upload size={22} className="text-slate-400" />
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Clique para selecionar ou arraste o CSV
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-3 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20 px-4 py-3 mb-3">
            <FileCheck2 size={18} className="text-emerald-500 shrink-0" />
            <p className="text-sm text-slate-800 dark:text-slate-200 flex-1 truncate">{arquivo.name}</p>
            <button onClick={() => { setArquivo(null); setPreview([]); }} className="text-slate-400 hover:text-slate-600">
              <X size={14} />
            </button>
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept=".csv,.txt"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) { setArquivo(f); parsePreview(f); }
            e.target.value = "";
          }}
        />

        {preview.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-medium text-slate-500 mb-2">
              Pré-visualização ({preview.length} linha{preview.length > 1 ? "s" : ""} de até 10):
            </p>
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 dark:bg-slate-700/60">
                  <tr>
                    <th className="px-3 py-2 text-left text-slate-500 font-medium">Competência</th>
                    <th className="px-3 py-2 text-right text-slate-500 font-medium">Salário</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.map((r, i) => (
                    <tr key={i} className="border-t border-slate-100 dark:border-slate-700">
                      <td className="px-3 py-1.5 font-mono text-slate-700 dark:text-slate-300">{r.competencia}</td>
                      <td className="px-3 py-1.5 text-right text-slate-700 dark:text-slate-300">{r.salario}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 mt-5">
          <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button
            type="button"
            loading={mutation.isPending}
            disabled={!arquivo}
            onClick={() => arquivo && mutation.mutate(arquivo)}
          >
            <Upload size={14} /> Importar
          </Button>
        </div>
      </motion.div>
    </div>
  );
}

// ─── Tab Remunerações ─────────────────────────────────────────────────────────
function TabRemuneracoes({ cnisId }: { cnisId: string }) {
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [modalNova, setModalNova] = useState(false);
  const [modalCSV, setModalCSV] = useState(false);
  const [editando, setEditando] = useState<RemuneracaoItem | null>(null);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["cnis", cnisId, "remuneracoes", page],
    queryFn: () => cnisService.listarRemuneracoes(cnisId, { skip: page * limit, limit }),
  });

  const deletarMutation = useMutation({
    mutationFn: (remId: string) => cnisService.deletarRemuneracao(cnisId, remId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cnis", cnisId, "remuneracoes"] });
      qc.invalidateQueries({ queryKey: ["cnis", cnisId] });
      toast.success("Remuneração removida.");
    },
    onError: () => toast.error("Erro ao remover."),
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 1;

  return (
    <>
      <AnimatePresence>
        {modalNova && <ModalNovaRemuneracao cnisId={cnisId} onClose={() => setModalNova(false)} />}
        {modalCSV && <ModalImportarCSV cnisId={cnisId} onClose={() => setModalCSV(false)} />}
        {editando && (
          <ModalEditarRemuneracao
            cnisId={cnisId}
            remuneracao={editando}
            onClose={() => setEditando(null)}
          />
        )}
      </AnimatePresence>

      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <p className="text-sm text-slate-500">
            {data ? `${data.total} remuneração(ões) cadastrada(s)` : "Carregando..."}
          </p>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setModalCSV(true)}>
              <Upload size={14} /> Importar CSV
            </Button>
            <Button onClick={() => setModalNova(true)}>
              <Plus size={14} /> Nova Remuneração
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-10">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          </div>
        ) : !data?.items.length ? (
          <Card className="py-16 flex flex-col items-center text-center">
            <DollarSign size={32} className="text-slate-300 mb-3" />
            <p className="font-medium text-slate-600 dark:text-slate-300">Nenhuma remuneração cadastrada</p>
            <p className="text-sm text-slate-400 mt-1">Adicione manualmente ou importe via CSV.</p>
          </Card>
        ) : (
          <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-700/60">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Competência</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide">Salário Contrib.</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wide hidden sm:table-cell">Corrigido</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wide hidden md:table-cell">Tipo</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wide hidden md:table-cell">Status</th>
                  <th className="px-4 py-3 w-20" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data.items.map((rem: RemuneracaoItem) => (
                  <tr key={rem.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-slate-800 dark:text-slate-200">
                      {String(rem.mes).padStart(2, "0")}/{rem.ano}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-700 dark:text-slate-300">
                      {BRL_FMT(rem.salario_contribuicao)}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-500 hidden sm:table-cell">
                      {rem.salario_contribuicao_corrigido != null ? BRL_FMT(rem.salario_contribuicao_corrigido) : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-500 hidden md:table-cell">
                      {rem.tipo_remuneracao ? TIPOS_REMUNERACAO[rem.tipo_remuneracao] : "—"}
                    </td>
                    <td className="px-4 py-3 text-center hidden md:table-cell">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        !rem.salario_valido
                          ? "bg-rose-50 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400"
                          : rem.acima_teto
                          ? "bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400"
                          : "bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
                      }`}>
                        {!rem.salario_valido ? "Inválido" : rem.acima_teto ? "Acima teto" : "OK"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => setEditando(rem)}
                          className="rounded p-1 text-slate-300 hover:text-indigo-500 transition-colors"
                          title="Editar"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm("Remover esta remuneração?")) deletarMutation.mutate(rem.id);
                          }}
                          className="rounded p-1 text-slate-300 hover:text-rose-500 transition-colors"
                          title="Remover"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">
              Página {page + 1} de {totalPages}
            </span>
            <div className="flex gap-2">
              <Button variant="secondary" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                Anterior
              </Button>
              <Button variant="secondary" disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>
                Próxima
              </Button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export function CNISDetalhes() {
  const { cnisId } = useParams<{ cnisId: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("geral");

  const { data: cnis, isLoading, isError } = useQuery({
    queryKey: ["cnis", cnisId],
    queryFn: () => cnisService.get(cnisId!),
    enabled: !!cnisId,
    retry: false,
  });

  const { data: calculos } = useQuery({
    queryKey: ["cnis", cnisId, "calculos"],
    queryFn: () => cnisService.listarCalculos(cnisId!),
    enabled: !!cnisId && tab === "calculos",
  });

  const { data: inconsistencias } = useQuery({
    queryKey: ["cnis", cnisId, "inconsistencias"],
    queryFn: () => cnisService.analisarInconsistencias(cnisId!),
    enabled: !!cnisId && tab === "inconsistencias",
  });

  if (isLoading) {
    return (
      <PageTransition>
        <div className="flex items-center justify-center h-64">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
        </div>
      </PageTransition>
    );
  }

  if (isError || !cnis) {
    return (
      <PageTransition>
        <div className="flex flex-col items-center justify-center h-64 gap-3">
          <p className="text-slate-500 dark:text-slate-400">CNIS não encontrado.</p>
          <button
            onClick={() => navigate("/cnis")}
            className="text-sm text-indigo-600 hover:underline"
          >
            Voltar para a lista
          </button>
        </div>
      </PageTransition>
    );
  }

  const fmt = (d: string | null) => {
    if (!d) return "—";
    const [y, m] = d.split("-");
    return `${m}/${y}`;
  };

  return (
    <PageTransition>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/cnis")}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Extrato CNIS
            </h1>
            <p className="mt-1 text-sm text-slate-500 font-mono">{cnis.nis}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => navigate(`/cnis/${cnisId}/simular`)}>
              <TrendingUp size={15} />
              Simular
            </Button>
            <Button onClick={() => navigate(`/cnis/${cnisId}/calcular`)}>
              <Calculator size={15} />
              Calcular RMI
            </Button>
          </div>
        </div>

        {/* Resumo */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard
            label="Tempo de Contribuição"
            value={cnis.tempo_contribuicao_anos != null ? `${Number(cnis.tempo_contribuicao_anos).toFixed(1)} anos` : "—"}
            sub={cnis.tempo_contribuicao_total_dias ? `${cnis.tempo_contribuicao_total_dias} dias` : undefined}
          />
          <SummaryCard
            label="Total Contribuições"
            value={cnis.total_contribuicoes?.toString() ?? "—"}
            sub="competências"
          />
          <SummaryCard
            label="Média Salarial"
            value={cnis.media_salarios_contribuicao != null ? BRL(cnis.media_salarios_contribuicao) : "—"}
            sub="salário médio de contribuição"
          />
          <SummaryCard
            label="Período"
            value={`${fmt(cnis.periodo_inicial_cn)} → ${fmt(cnis.periodo_final_cn)}`}
            sub="competências no CNIS"
          />
        </div>

        {/* Tabs */}
        <div>
          <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700">
            {(["geral", "remuneracoes", "calculos", "inconsistencias"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                  tab === t
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
              >
                {t === "geral" && "Visão Geral"}
                {t === "remuneracoes" && "Remunerações"}
                {t === "calculos" && `Cálculos${calculos?.length ? ` (${calculos.length})` : ""}`}
                {t === "inconsistencias" && `Inconsistências${inconsistencias ? ` (${inconsistencias.total_inconsistencias})` : ""}`}
              </button>
            ))}
          </div>

          <div className="mt-4">
            {tab === "geral" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-5 space-y-3">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">Dados do Segurado</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">NIS/PIS</span>
                      <span className="font-mono text-slate-800 dark:text-slate-200">{cnis.nis}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Data de Nascimento</span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {cnis.data_nascimento ? new Date(cnis.data_nascimento + "T12:00").toLocaleDateString("pt-BR") : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Maior Salário</span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {cnis.maior_salario_contribuicao != null ? BRL(cnis.maior_salario_contribuicao) : "—"}
                      </span>
                    </div>
                  </div>
                </Card>
                <Card className="p-5 space-y-3">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">Status do Processamento</p>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                      cnis.status_processamento === "concluido"
                        ? "bg-emerald-50 text-emerald-700"
                        : cnis.status_processamento === "erro"
                        ? "bg-rose-50 text-rose-700"
                        : "bg-yellow-50 text-yellow-700"
                    }`}>
                      {cnis.status_processamento}
                    </span>
                  </div>
                  {cnis.erros_validacao && (
                    <pre className="text-xs bg-rose-50 dark:bg-rose-900/20 text-rose-700 dark:text-rose-300 rounded p-2 overflow-auto max-h-32">
                      {JSON.stringify(cnis.erros_validacao, null, 2)}
                    </pre>
                  )}
                  <p className="text-xs text-slate-400">
                    Importado em {new Date(cnis.created_at).toLocaleString("pt-BR")}
                  </p>
                </Card>
              </div>
            )}

            {tab === "remuneracoes" && <TabRemuneracoes cnisId={cnisId!} />}

            {tab === "calculos" && (
              <div className="space-y-4">
                {!calculos?.length ? (
                  <Card className="py-16 flex flex-col items-center text-center">
                    <Calculator size={32} className="text-slate-300 mb-3" />
                    <p className="font-medium text-slate-600 dark:text-slate-300">Nenhum cálculo realizado</p>
                    <p className="text-sm text-slate-400 mt-1">Execute um cálculo de RMI para este CNIS.</p>
                    <Button className="mt-4" onClick={() => navigate(`/cnis/${cnisId}/calcular`)}>
                      <Calculator size={14} /> Calcular RMI
                    </Button>
                  </Card>
                ) : (
                  calculos.map((c) => <CalculoCard key={c.id} calculo={c} />)
                )}
              </div>
            )}

            {tab === "inconsistencias" && (
              <div className="space-y-3">
                {!inconsistencias ? (
                  <div className="flex justify-center py-8">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
                  </div>
                ) : inconsistencias.total_inconsistencias === 0 ? (
                  <Card className="py-12 flex flex-col items-center text-center">
                    <CheckCircle2 size={32} className="text-emerald-400 mb-3" />
                    <p className="font-medium text-slate-600 dark:text-slate-300">Nenhuma inconsistência encontrada</p>
                    <p className="text-sm text-slate-400 mt-1">O CNIS está sem irregularidades detectadas.</p>
                  </Card>
                ) : (
                  <>
                    <div className="flex items-center gap-2 text-sm text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-4 py-3">
                      <AlertTriangle size={15} className="shrink-0" />
                      <span>{inconsistencias.total_inconsistencias} inconsistência(s) encontrada(s) — revisão recomendada.</span>
                    </div>
                    {inconsistencias.inconsistencias.map((item, i) => (
                      <Card key={i} className="p-4 space-y-1.5">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{item.descricao}</p>
                            {item.periodo_afetado && (
                              <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                                <Calendar size={11} /> {item.periodo_afetado}
                              </p>
                            )}
                          </div>
                          <span className="text-xs bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded px-2 py-0.5 shrink-0 font-mono">
                            {item.tipo}
                          </span>
                        </div>
                        {item.recomendacao && (
                          <p className="text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-700/50 rounded px-2.5 py-1.5">
                            💡 {item.recomendacao}
                          </p>
                        )}
                      </Card>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
