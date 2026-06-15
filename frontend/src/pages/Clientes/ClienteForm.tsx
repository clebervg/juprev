import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowLeft, Plus, Trash2, Loader2 } from "lucide-react";
import { clientsService, fetchCep } from "@/services/clients";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { masks } from "@/utils/masks";

// ─── Schema ─────────────────────────────────────────────────────────────────

function validarCPF(cpf: string): boolean {
  const d = cpf.replace(/\D/g, "");
  if (d.length !== 11 || new Set(d).size === 1) return false;
  for (let i = 0; i < 2; i++) {
    const total = d.slice(0, 9 + i).split("").reduce((s, n, j) => s + +n * (10 + i - j), 0);
    let r = (total * 10) % 11;
    if (r === 10) r = 0;
    if (r !== +d[9 + i]) return false;
  }
  return true;
}

const dependenteSchema = z.object({
  nome: z.string().min(2, "Nome obrigatório"),
  cpf: z.string().optional().refine((v) => !v || validarCPF(v), "CPF inválido"),
  data_nascimento: z.string().optional(),
  parentesco: z.enum(["filho", "conjuge", "companheiro", "outros", ""]).optional(),
  e_beneficiario: z.boolean().default(false),
  percentual_dependencia: z.coerce.number().min(0).max(100).optional(),
});

const str = z.string().optional();

const schema = z.object({
  nome: z.string().min(2, "Nome obrigatório"),
  cpf: str,
  rg: str,
  rg_orgao_expedidor: str,
  data_nascimento: str,
  nome_mae: str,
  nome_pai: str,
  estado_civil: str,
  genero: str,
  nis: str,
  ctps_numero: str,
  ctps_serie: str,
  escolaridade: str,
  profissao: str,
  email: str,
  telefone_celular: str,
  whatsapp: z.boolean().default(true),
  telefone_fixo: str,
  contato_emergencia_nome: str,
  contato_emergencia_telefone: str,
  cep: str,
  logradouro: str,
  numero: str,
  complemento: str,
  bairro: str,
  cidade: str,
  uf: str,
  tipo_residencia: str,
  renda_mensal: str,
  possui_deficiencia: z.boolean().default(false),
  tipo_deficiencia: str,
  tempo_contribuicao_anos: str,
  observacoes: str,
  dependentes: z.array(dependenteSchema).default([]),
});

type FormData = z.infer<typeof schema>;

// ─── Helpers ────────────────────────────────────────────────────────────────

function Field({
  label,
  error,
  required,
  children,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
        {label} {required && <span className="text-rose-500">*</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-rose-600" role="alert">{error}</p>}
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:bg-slate-50 dark:disabled:bg-slate-800";

const selectCls = inputCls;

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="col-span-full border-b border-slate-100 dark:border-slate-700 pb-2 mb-2">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{children}</h3>
    </div>
  );
}

// ─── Componente ─────────────────────────────────────────────────────────────

export function ClienteForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [cepLoading, setCepLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
    control,
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const { fields: depFields, append: depAppend, remove: depRemove } = useFieldArray({
    control,
    name: "dependentes",
  });

  const possuiDeficiencia = watch("possui_deficiencia");

  // Carrega dados para edição
  useEffect(() => {
    if (!id) return;
    clientsService.get(id).then((client) => {
      // Aplica máscaras nos campos formatados antes de popular o formulário.
      const data: Record<string, unknown> = {
        ...client,
        cpf: client.cpf ? masks.cpf(client.cpf) : "",
        nis: client.nis ? masks.nis(client.nis) : "",
        telefone_celular: client.telefone_celular ? masks.telefone(client.telefone_celular) : "",
        telefone_fixo: client.telefone_fixo ? masks.telefone(client.telefone_fixo) : "",
        contato_emergencia_telefone: client.contato_emergencia_telefone
          ? masks.telefone(client.contato_emergencia_telefone)
          : "",
        cep: client.cep ? masks.cep(client.cep) : "",
        renda_mensal: client.renda_mensal != null ? String(client.renda_mensal) : "",
        tempo_contribuicao_anos: client.tempo_contribuicao_anos != null
          ? String(client.tempo_contribuicao_anos)
          : "",
      };

      // Popula o formulário — null vira string vazia para campos de texto.
      Object.entries(data).forEach(([k, v]) => {
        if (k === "id" || k === "tenant_id" || k === "created_at") return;
        setValue(
          k as keyof FormData,
          (v === null ? "" : v) as never,
          { shouldDirty: false },
        );
      });
    });
  }, [id, setValue]);

  // Busca CEP
  const handleCepBlur = async (e: React.FocusEvent<HTMLInputElement>) => {
    const cep = e.target.value.replace(/\D/g, "");
    if (cep.length !== 8) return;
    setCepLoading(true);
    const addr = await fetchCep(cep);
    setCepLoading(false);
    if (addr) {
      // Só sobrescreve campos que o ViaCEP retornou com valor —
      // CEPs de bairro/cidade retornam logradouro vazio, não queremos apagar o que o usuário digitou.
      const opts = { shouldDirty: true, shouldValidate: true } as const;
      if (addr.logradouro) setValue("logradouro", addr.logradouro, opts);
      if (addr.bairro) setValue("bairro", addr.bairro, opts);
      if (addr.localidade) setValue("cidade", addr.localidade, opts);
      if (addr.uf) setValue("uf", addr.uf, opts);
    } else {
      toast.error("CEP não encontrado.");
    }
  };

  const onSubmit = async (data: FormData) => {
    try {
      // Strings vazias viram undefined — Pydantic rejeita "" em campos opcionais/enum.
      const n = (v: string | undefined) => v || undefined;
      // Remove máscaras de formatação antes de enviar.
      const digits = (v: string | undefined) => v?.replace(/\D/g, "") || undefined;

      const payload = {
        nome: data.nome,
        // Dados pessoais
        cpf: digits(data.cpf),
        rg: n(data.rg),
        rg_orgao_expedidor: n(data.rg_orgao_expedidor),
        data_nascimento: n(data.data_nascimento),
        nome_mae: n(data.nome_mae),
        nome_pai: n(data.nome_pai),
        estado_civil: n(data.estado_civil),
        genero: n(data.genero),
        nis: digits(data.nis),
        ctps_numero: n(data.ctps_numero),
        ctps_serie: n(data.ctps_serie),
        escolaridade: n(data.escolaridade),
        profissao: n(data.profissao),
        tempo_contribuicao_anos: data.tempo_contribuicao_anos ? parseInt(data.tempo_contribuicao_anos) : undefined,
        // Contato
        email: n(data.email),
        telefone_celular: digits(data.telefone_celular),
        whatsapp: data.whatsapp,
        telefone_fixo: digits(data.telefone_fixo),
        contato_emergencia_nome: n(data.contato_emergencia_nome),
        contato_emergencia_telefone: digits(data.contato_emergencia_telefone),
        // Endereço
        cep: digits(data.cep),
        logradouro: n(data.logradouro),
        numero: n(data.numero),
        complemento: n(data.complemento),
        bairro: n(data.bairro),
        cidade: n(data.cidade),
        uf: n(data.uf),
        tipo_residencia: n(data.tipo_residencia),
        // Dados adicionais
        renda_mensal: data.renda_mensal ? parseFloat(data.renda_mensal) : undefined,
        possui_deficiencia: data.possui_deficiencia,
        tipo_deficiencia: n(data.tipo_deficiencia),
        observacoes: n(data.observacoes),
        // Dependentes
        dependentes: data.dependentes.map((d) => ({
          nome: d.nome,
          cpf: digits(d.cpf),
          data_nascimento: n(d.data_nascimento),
          parentesco: n(d.parentesco),
          e_beneficiario: d.e_beneficiario,
          percentual_dependencia: d.percentual_dependencia || undefined,
        })),
      };
      if (isEdit && id) {
        await clientsService.update(id, payload);
        toast.success("Cliente atualizado com sucesso.");
      } else {
        await clientsService.create(payload);
        toast.success("Cliente cadastrado com sucesso.");
        navigate("/clientes");
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg ?? "Erro ao salvar cliente.");
    }
  };

  return (
    <PageTransition>
      <div className="space-y-6 max-w-5xl">
        {/* Header */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/clientes")}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Voltar"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              {isEdit ? "Editar Cliente" : "Novo Cliente"}
            </h1>
            <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
              Preencha os dados do cliente previdenciário.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">

          {/* Dados pessoais */}
          <Card className="p-6">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <SectionTitle>Dados Pessoais</SectionTitle>

              <Field label="Nome completo" error={errors.nome?.message} required>
                <input {...register("nome")} className={inputCls} placeholder="Nome completo" />
              </Field>

              <Field label="CPF" error={errors.cpf?.message} required>
                <input
                  {...register("cpf")}
                  className={inputCls}
                  placeholder="000.000.000-00"
                  onChange={(e) => setValue("cpf", masks.cpf(e.target.value))}
                  maxLength={14}
                />
              </Field>

              <Field label="RG" error={errors.rg?.message} required>
                <input {...register("rg")} className={inputCls} placeholder="RG" />
              </Field>

              <Field label="Órgão expedidor" error={errors.rg_orgao_expedidor?.message}>
                <input {...register("rg_orgao_expedidor")} className={inputCls} placeholder="Ex: SSP-SP" />
              </Field>

              <Field label="Data de nascimento" error={errors.data_nascimento?.message} required>
                <input {...register("data_nascimento")} type="date" className={inputCls} />
              </Field>

              <Field label="Nome da mãe" error={errors.nome_mae?.message} required>
                <input {...register("nome_mae")} className={inputCls} placeholder="Nome completo da mãe" />
              </Field>

              <Field label="Nome do pai" error={errors.nome_pai?.message}>
                <input {...register("nome_pai")} className={inputCls} placeholder="Nome completo do pai" />
              </Field>

              <Field label="Estado civil" error={errors.estado_civil?.message}>
                <select {...register("estado_civil")} className={selectCls}>
                  <option value="">Selecione...</option>
                  <option value="solteiro">Solteiro(a)</option>
                  <option value="casado">Casado(a)</option>
                  <option value="divorciado">Divorciado(a)</option>
                  <option value="viuvo">Viúvo(a)</option>
                  <option value="uniao_estavel">União Estável</option>
                </select>
              </Field>

              <Field label="Gênero" error={errors.genero?.message}>
                <select {...register("genero")} className={selectCls}>
                  <option value="">Selecione...</option>
                  <option value="masculino">Masculino</option>
                  <option value="feminino">Feminino</option>
                  <option value="outro">Outro</option>
                </select>
              </Field>

              <Field label="NIS / PIS / PASEP" error={errors.nis?.message}>
                <input
                  {...register("nis")}
                  className={inputCls}
                  placeholder="000.00000.00-0 (opcional)"
                  onChange={(e) => setValue("nis", masks.nis(e.target.value))}
                  maxLength={14}
                />
              </Field>

              <Field label="CTPS — Número" error={errors.ctps_numero?.message}>
                <input {...register("ctps_numero")} className={inputCls} placeholder="Número CTPS" />
              </Field>

              <Field label="CTPS — Série" error={errors.ctps_serie?.message}>
                <input {...register("ctps_serie")} className={inputCls} placeholder="Série" />
              </Field>

              <Field label="Escolaridade">
                <select {...register("escolaridade")} className={selectCls}>
                  <option value="">Selecione...</option>
                  {["Analfabeto", "Fundamental incompleto", "Fundamental completo", "Médio incompleto", "Médio completo", "Superior incompleto", "Superior completo", "Pós-graduação"].map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </Field>

              <Field label="Profissão / Ocupação">
                <input {...register("profissao")} className={inputCls} placeholder="Ex: Agricultor" />
              </Field>

              <Field label="Tempo de contribuição (anos)">
                <input {...register("tempo_contribuicao_anos")} type="number" min={0} max={50} className={inputCls} placeholder="Ex: 15" />
              </Field>
            </div>
          </Card>

          {/* Contato */}
          <Card className="p-6">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <SectionTitle>Contato</SectionTitle>

              <Field label="E-mail" error={errors.email?.message}>
                <input {...register("email")} type="email" className={inputCls} placeholder="email@exemplo.com" />
              </Field>

              <Field label="Celular" error={errors.telefone_celular?.message}>
                <input
                  {...register("telefone_celular")}
                  className={inputCls}
                  placeholder="(00) 00000-0000"
                  onChange={(e) => setValue("telefone_celular", masks.telefone(e.target.value))}
                  maxLength={15}
                />
              </Field>

              <Field label="WhatsApp?">
                <label className="flex items-center gap-2 mt-2 cursor-pointer">
                  <input {...register("whatsapp")} type="checkbox" className="h-4 w-4 rounded border-slate-300 text-indigo-600" />
                  <span className="text-sm text-slate-600 dark:text-slate-400">Mesmo número tem WhatsApp</span>
                </label>
              </Field>

              <Field label="Telefone fixo">
                <input
                  {...register("telefone_fixo")}
                  className={inputCls}
                  placeholder="(00) 0000-0000"
                  onChange={(e) => setValue("telefone_fixo", masks.telefone(e.target.value))}
                  maxLength={14}
                />
              </Field>

              <Field label="Contato de emergência — Nome">
                <input {...register("contato_emergencia_nome")} className={inputCls} placeholder="Nome" />
              </Field>

              <Field label="Contato de emergência — Telefone">
                <input
                  {...register("contato_emergencia_telefone")}
                  className={inputCls}
                  placeholder="(00) 00000-0000"
                  onChange={(e) => setValue("contato_emergencia_telefone", masks.telefone(e.target.value))}
                  maxLength={15}
                />
              </Field>
            </div>
          </Card>

          {/* Endereço */}
          <Card className="p-6">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <SectionTitle>Endereço</SectionTitle>

              <Field label="CEP">
                <div className="relative">
                  <input
                    {...register("cep")}
                    className={inputCls}
                    placeholder="00000-000"
                    onChange={(e) => setValue("cep", masks.cep(e.target.value))}
                    onBlur={handleCepBlur}
                    maxLength={9}
                  />
                  {cepLoading && (
                    <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-slate-400" />
                  )}
                </div>
              </Field>

              <Field label="Logradouro">
                <input {...register("logradouro")} className={inputCls} placeholder="Rua, Av..." />
              </Field>

              <Field label="Número">
                <input {...register("numero")} className={inputCls} placeholder="Ex: 123" />
              </Field>

              <Field label="Complemento">
                <input {...register("complemento")} className={inputCls} placeholder="Apto, Bloco..." />
              </Field>

              <Field label="Bairro">
                <input {...register("bairro")} className={inputCls} placeholder="Bairro" />
              </Field>

              <Field label="Cidade">
                <input {...register("cidade")} className={inputCls} placeholder="Cidade" />
              </Field>

              <Field label="UF" error={errors.uf?.message}>
                <input {...register("uf")} className={inputCls} placeholder="Ex: SP" maxLength={2} />
              </Field>

              <Field label="Tipo de residência">
                <select {...register("tipo_residencia")} className={selectCls}>
                  <option value="">Selecione...</option>
                  <option value="propria">Própria</option>
                  <option value="alugada">Alugada</option>
                  <option value="cedida">Cedida</option>
                  <option value="outras">Outras</option>
                </select>
              </Field>
            </div>
          </Card>

          {/* Dados adicionais */}
          <Card className="p-6">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <SectionTitle>Dados Adicionais</SectionTitle>

              <Field label="Renda mensal (R$)">
                <input {...register("renda_mensal")} type="number" min={0} step={0.01} className={inputCls} placeholder="Ex: 1.412,00" />
              </Field>

              <Field label="Possui deficiência?">
                <label className="flex items-center gap-2 mt-2 cursor-pointer">
                  <input {...register("possui_deficiencia")} type="checkbox" className="h-4 w-4 rounded border-slate-300 text-indigo-600" />
                  <span className="text-sm text-slate-600 dark:text-slate-400">Sim, possui deficiência</span>
                </label>
              </Field>

              {possuiDeficiencia && (
                <Field label="Tipo de deficiência">
                  <input {...register("tipo_deficiencia")} className={inputCls} placeholder="Descreva o tipo" />
                </Field>
              )}

              <Field label="Observações" error={errors.observacoes?.message}>
                <textarea
                  {...register("observacoes")}
                  className={`${inputCls} resize-none`}
                  rows={3}
                  placeholder="Informações adicionais relevantes para o processo..."
                />
              </Field>
            </div>
          </Card>

          {/* Dependentes */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Dependentes</h3>
                <p className="text-xs text-slate-400 mt-0.5">Filhos, cônjuge e outros dependentes</p>
              </div>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => depAppend({ nome: "", e_beneficiario: false })}
              >
                <Plus size={14} /> Adicionar
              </Button>
            </div>

            {depFields.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-4">Nenhum dependente adicionado.</p>
            ) : (
              <div className="space-y-4">
                {depFields.map((field, idx) => (
                  <div key={field.id} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 rounded-lg border border-slate-100 dark:border-slate-700 p-4">
                    <Field label="Nome" error={errors.dependentes?.[idx]?.nome?.message} required>
                      <input {...register(`dependentes.${idx}.nome`)} className={inputCls} placeholder="Nome completo" />
                    </Field>
                    <Field label="CPF" error={errors.dependentes?.[idx]?.cpf?.message}>
                      <input
                        {...register(`dependentes.${idx}.cpf`)}
                        className={inputCls}
                        placeholder="000.000.000-00"
                        onChange={(e) => setValue(`dependentes.${idx}.cpf`, masks.cpf(e.target.value))}
                        maxLength={14}
                      />
                    </Field>
                    <Field label="Data de nascimento">
                      <input {...register(`dependentes.${idx}.data_nascimento`)} type="date" className={inputCls} />
                    </Field>
                    <Field label="Parentesco">
                      <select {...register(`dependentes.${idx}.parentesco`)} className={selectCls}>
                        <option value="">Selecione...</option>
                        <option value="filho">Filho(a)</option>
                        <option value="conjuge">Cônjuge</option>
                        <option value="companheiro">Companheiro(a)</option>
                        <option value="outros">Outros</option>
                      </select>
                    </Field>
                    <Field label="% Dependência">
                      <input {...register(`dependentes.${idx}.percentual_dependencia`)} type="number" min={0} max={100} className={inputCls} placeholder="Ex: 100" />
                    </Field>
                    <div className="flex items-end gap-4">
                      <label className="flex items-center gap-2 mt-2 cursor-pointer flex-1">
                        <input {...register(`dependentes.${idx}.e_beneficiario`)} type="checkbox" className="h-4 w-4 rounded border-slate-300 text-indigo-600" />
                        <span className="text-sm text-slate-600 dark:text-slate-400">É beneficiário</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => depRemove(idx)}
                        className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950 transition-colors"
                        aria-label="Remover dependente"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Ações */}
          <div className="flex items-center justify-end gap-3 pb-6">
            <Button type="button" variant="secondary" onClick={() => navigate("/clientes")}>
              Cancelar
            </Button>
            <Button type="submit" loading={isSubmitting}>
              {isEdit ? "Salvar alterações" : "Cadastrar cliente"}
            </Button>
          </div>
        </form>
      </div>
    </PageTransition>
  );
}
