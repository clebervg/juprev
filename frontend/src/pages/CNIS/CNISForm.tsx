import { useRef, useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, FilePlus, Upload, FileCheck2, X, Lock, Search, UserCheck, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import { cnisService } from "@/services/cnis";
import { clientsService } from "@/services/clients";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const TIPOS_ACEITOS = [".xml", ".pdf", ".txt"];
const MAX_MB = 10;

const schema = z.object({
  cliente_id: z.string().uuid("Selecione um cliente"),
  nome_segurado: z.string().min(2, "Nome obrigatório"),
  cpf: z.string().length(11, "CPF deve ter 11 dígitos (somente números)"),
  nis: z.string().length(11, "NIS deve ter 11 dígitos").optional().or(z.literal("")),
  data_nascimento: z.string().min(1, "Data obrigatória"),
});

type FormData = z.infer<typeof schema>;

function Field({
  label,
  error,
  children,
  locked,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
  locked?: boolean;
}) {
  return (
    <div>
      <label className="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
        {label}
        {locked && <Lock size={11} className="text-slate-400" />}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-rose-500">{error}</p>}
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20";

const inputLockedCls =
  "w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2 text-sm text-slate-500 dark:text-slate-400 cursor-not-allowed select-none";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function CNISForm() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const inputFileRef = useRef<HTMLInputElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [processando, setProcessando] = useState(false);

  // Combobox state
  const [busca, setBusca] = useState("");
  const [query, setQuery] = useState("");
  const [aberto, setAberto] = useState(false);
  const [clienteSelecionado, setClienteSelecionado] = useState<{ id: string; nome: string } | null>(null);

  // Debounce: só dispara a query 300ms após parar de digitar
  useEffect(() => {
    const t = setTimeout(() => setQuery(busca), 300);
    return () => clearTimeout(t);
  }, [busca]);

  const { data: clientesData, isFetching: buscando } = useQuery({
    queryKey: ["clients-search", query],
    queryFn: () => clientsService.list({ limit: 20, search: query || undefined }),
    enabled: aberto,
  });

  // Fecha o dropdown ao clicar fora
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setAberto(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const {
    register,
    handleSubmit,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const selecionarCliente = useCallback(async (id: string, nome: string) => {
    setClienteSelecionado({ id, nome });
    setAberto(false);
    setValue("cliente_id", id, { shouldValidate: true });
    try {
      const cliente = await qc.fetchQuery({
        queryKey: ["clients", id],
        queryFn: () => clientsService.get(id),
        staleTime: 5 * 60 * 1000,
      });
      setValue("nome_segurado", cliente.nome, { shouldDirty: true });
      if (cliente.data_nascimento) setValue("data_nascimento", cliente.data_nascimento, { shouldDirty: true });
      if (cliente.cpf) setValue("cpf", cliente.cpf, { shouldDirty: true });
      if (cliente.nis) setValue("nis", cliente.nis, { shouldDirty: true });
    } catch {
      toast.error("Erro ao carregar dados do cliente.");
    }
  }, [qc, setValue]);

  const limparCliente = () => {
    setClienteSelecionado(null);
    setBusca("");
    setQuery("");
    setValue("cliente_id", "", { shouldValidate: false });
    setValue("nome_segurado", "");
    setValue("data_nascimento", "");
    setValue("cpf", "");
    setValue("nis", "");
  };

  const criarMutation = useMutation({
    mutationFn: async (data: FormData) => {
      const cnis = await cnisService.create({
        ...data,
        arquivo_original_nome: arquivo?.name,
      });

      // Se houver PDF, processa automaticamente
      if (arquivo && arquivo.name.toLowerCase().endsWith(".pdf")) {
        setProcessando(true);
        try {
          const resultado = await cnisService.processarPDF(cnis.id, arquivo);
          toast.success(
            `CNIS importado: ${resultado.criadas} remunerações registradas.`,
          );
        } catch {
          toast.warning(
            "CNIS registrado, mas houve erro ao processar o PDF. Tente importar novamente na página de detalhes.",
          );
        } finally {
          setProcessando(false);
        }
      } else {
        toast.success("CNIS registrado com sucesso.");
      }

      return cnis;
    },
    onSuccess: (cnis) => {
      navigate(`/cnis/${cnis.id}`);
    },
    onError: () => toast.error("Erro ao registrar CNIS."),
  });

  const validarArquivo = (file: File): boolean => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!TIPOS_ACEITOS.includes(ext)) {
      toast.error(`Tipo inválido. Aceitos: ${TIPOS_ACEITOS.join(", ")}`);
      return false;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      toast.error(`Arquivo muito grande. Máximo: ${MAX_MB} MB`);
      return false;
    }
    return true;
  };

  const onFileSelect = (file: File) => {
    if (validarArquivo(file)) setArquivo(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFileSelect(file);
  };

  const isLoading = criarMutation.isPending || processando;

  return (
    <PageTransition>
      <div className="max-w-2xl space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/cnis")}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Importar CNIS
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Registre os dados do extrato CNIS do segurado
            </p>
          </div>
        </div>

        <Card className="p-6">
          <form
            onSubmit={handleSubmit((d) => criarMutation.mutate(d))}
            className="space-y-5"
          >
            {/* Campo de busca de cliente com autocomplete */}
            <input type="hidden" {...register("cliente_id")} />
            <div>
              <label className="flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Cliente
              </label>

              {clienteSelecionado ? (
                <div className="flex items-center gap-3 rounded-lg border border-indigo-200 dark:border-indigo-700 bg-indigo-50 dark:bg-indigo-900/20 px-3 py-2.5">
                  <UserCheck size={16} className="text-indigo-500 shrink-0" />
                  <span className="flex-1 text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                    {clienteSelecionado.nome}
                  </span>
                  <button
                    type="button"
                    onClick={limparCliente}
                    className="shrink-0 rounded-md p-1 text-slate-400 hover:bg-indigo-100 dark:hover:bg-indigo-800 hover:text-slate-600 transition-colors"
                    aria-label="Trocar cliente"
                  >
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <div className="relative" ref={dropdownRef}>
                  <div className="relative">
                    <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                    <input
                      ref={searchRef}
                      type="text"
                      value={busca}
                      onChange={(e) => { setBusca(e.target.value); setAberto(true); }}
                      onFocus={() => setAberto(true)}
                      placeholder="Buscar por nome ou CPF..."
                      className={`${inputCls} pl-9 pr-8`}
                      autoComplete="off"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {buscando
                        ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
                        : <ChevronDown size={14} className="text-slate-400" />
                      }
                    </div>
                  </div>

                  <AnimatePresence>
                    {aberto && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.12 }}
                        className="absolute z-50 mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 shadow-lg overflow-hidden"
                      >
                        {!clientesData?.items.length ? (
                          <p className="px-4 py-3 text-sm text-slate-400">
                            {buscando ? "Buscando..." : busca ? "Nenhum cliente encontrado." : "Digite para buscar..."}
                          </p>
                        ) : (
                          <ul className="max-h-56 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700">
                            {clientesData.items.map((c) => (
                              <li key={c.id}>
                                <button
                                  type="button"
                                  onMouseDown={(e) => e.preventDefault()}
                                  onClick={() => selecionarCliente(c.id, c.nome)}
                                  className="w-full text-left px-4 py-2.5 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-colors"
                                >
                                  <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{c.nome}</p>
                                  <p className="text-xs text-slate-400 font-mono">{c.cpf_mascarado}</p>
                                </button>
                              </li>
                            ))}
                          </ul>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {errors.cliente_id && (
                <p className="mt-1 text-xs text-rose-500">{errors.cliente_id.message}</p>
              )}
            </div>

            {clienteSelecionado && (
              <p className="text-xs text-slate-400 -mt-2 flex items-center gap-1">
                <Lock size={10} />
                Dados carregados automaticamente. Clique no × para trocar de cliente.
              </p>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Nome do Segurado" error={errors.nome_segurado?.message} locked={!!clienteSelecionado}>
                {clienteSelecionado ? (
                  <input
                    readOnly
                    value={getValues("nome_segurado") ?? ""}
                    className={inputLockedCls}
                    tabIndex={-1}
                  />
                ) : (
                  <input
                    {...register("nome_segurado")}
                    placeholder="Nome completo"
                    className={inputCls}
                  />
                )}
              </Field>

              <Field label="Data de Nascimento" error={errors.data_nascimento?.message} locked={!!clienteSelecionado}>
                {clienteSelecionado ? (
                  <input
                    readOnly
                    type="date"
                    value={getValues("data_nascimento") ?? ""}
                    className={inputLockedCls}
                    tabIndex={-1}
                  />
                ) : (
                  <input type="date" {...register("data_nascimento")} className={inputCls} />
                )}
              </Field>

              <Field label="CPF (somente números)" error={errors.cpf?.message} locked={!!clienteSelecionado}>
                {clienteSelecionado ? (
                  <input
                    readOnly
                    value={getValues("cpf") ?? ""}
                    className={inputLockedCls}
                    tabIndex={-1}
                  />
                ) : (
                  <input
                    {...register("cpf")}
                    placeholder="00000000000"
                    maxLength={11}
                    className={inputCls}
                  />
                )}
              </Field>

              <Field label="NIS / PIS / PASEP (opcional)" error={errors.nis?.message} locked={!!clienteSelecionado}>
                {clienteSelecionado ? (
                  <input
                    readOnly
                    value={getValues("nis") ?? ""}
                    className={inputLockedCls}
                    tabIndex={-1}
                  />
                ) : (
                  <input
                    {...register("nis")}
                    placeholder="00000000000"
                    maxLength={11}
                    className={inputCls}
                  />
                )}
              </Field>
            </div>

            {/* Upload de arquivo */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Arquivo CNIS{" "}
                <span className="text-slate-400 font-normal">
                  (opcional — XML, PDF ou TXT, máx. {MAX_MB} MB)
                </span>
              </label>

              <AnimatePresence mode="wait">
                {arquivo ? (
                  <motion.div
                    key="arquivo-selecionado"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="flex items-center gap-3 rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20 px-4 py-3"
                  >
                    <FileCheck2 size={20} className="text-emerald-500 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                        {arquivo.name}
                      </p>
                      <p className="text-xs text-slate-400">{formatBytes(arquivo.size)}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setArquivo(null)}
                      className="shrink-0 rounded-md p-1 text-slate-400 hover:bg-emerald-100 dark:hover:bg-emerald-800 hover:text-slate-600 transition-colors"
                      aria-label="Remover arquivo"
                    >
                      <X size={14} />
                    </button>
                  </motion.div>
                ) : (
                  <motion.div
                    key="dropzone"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={onDrop}
                    onClick={() => inputFileRef.current?.click()}
                    className={`
                      flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed
                      cursor-pointer px-6 py-8 text-center transition-colors duration-200
                      ${isDragging
                        ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20"
                        : "border-slate-200 dark:border-slate-600 hover:border-indigo-300 dark:hover:border-indigo-600 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                      }
                    `}
                  >
                    <div className={`flex h-10 w-10 items-center justify-center rounded-full transition-colors ${
                      isDragging ? "bg-indigo-100 dark:bg-indigo-800" : "bg-slate-100 dark:bg-slate-700"
                    }`}>
                      <Upload size={18} className={isDragging ? "text-indigo-600" : "text-slate-400"} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Arraste o arquivo aqui ou{" "}
                        <span className="text-indigo-600 dark:text-indigo-400">clique para selecionar</span>
                      </p>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {TIPOS_ACEITOS.join(", ")} · máx. {MAX_MB} MB
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <input
                ref={inputFileRef}
                type="file"
                accept={TIPOS_ACEITOS.join(",")}
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) onFileSelect(file);
                  e.target.value = "";
                }}
              />
            </div>

            {processando && (
              <div className="flex items-center gap-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 px-4 py-3 text-sm text-indigo-700 dark:text-indigo-300">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent shrink-0" />
                Processando PDF e importando remunerações...
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="secondary" onClick={() => navigate("/cnis")} disabled={isLoading}>
                Cancelar
              </Button>
              <Button type="submit" loading={isLoading}>
                <FilePlus size={15} />
                {arquivo?.name.toLowerCase().endsWith(".pdf") ? "Registrar e Importar PDF" : "Registrar CNIS"}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </PageTransition>
  );
}
