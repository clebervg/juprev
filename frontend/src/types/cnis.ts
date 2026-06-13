export type StatusProcessamento = "pendente" | "processando" | "concluido" | "erro";

export type TipoBeneficio =
  | "aposentadoria_idade_urbana"
  | "aposentadoria_idade_rural"
  | "aposentadoria_tempo_contribuicao"
  | "aposentadoria_especial_15"
  | "aposentadoria_especial_20"
  | "aposentadoria_especial_25"
  | "aposentadoria_pcd_idade"
  | "aposentadoria_pcd_tempo"
  | "auxilio_doenca"
  | "aposentadoria_invalidez"
  | "salario_maternidade"
  | "pensao_morte";

export const TIPOS_BENEFICIO: Record<TipoBeneficio, string> = {
  aposentadoria_idade_urbana: "Aposentadoria por Idade (Urbana)",
  aposentadoria_idade_rural: "Aposentadoria por Idade (Rural)",
  aposentadoria_tempo_contribuicao: "Aposentadoria por Tempo de Contribuição",
  aposentadoria_especial_15: "Aposentadoria Especial (15 anos)",
  aposentadoria_especial_20: "Aposentadoria Especial (20 anos)",
  aposentadoria_especial_25: "Aposentadoria Especial (25 anos)",
  aposentadoria_pcd_idade: "Aposentadoria PCD por Idade",
  aposentadoria_pcd_tempo: "Aposentadoria PCD por Tempo",
  auxilio_doenca: "Auxílio-Doença",
  aposentadoria_invalidez: "Aposentadoria por Invalidez",
  salario_maternidade: "Salário-Maternidade",
  pensao_morte: "Pensão por Morte",
};

export interface CNISListItem {
  id: string;
  cliente_id: string;
  nis: string;
  periodo_inicial_cn: string | null;
  periodo_final_cn: string | null;
  tempo_contribuicao_anos: number | null;
  total_contribuicoes: number | null;
  status_processamento: StatusProcessamento;
  created_at: string;
}

export interface CNISListResponse {
  items: CNISListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface PeriodoContribuicao {
  id: string;
  cnpj_empregador: string | null;
  razao_social_empregador: string | null;
  data_inicio: string;
  data_fim: string | null;
  tipo_contribuinte: string | null;
  dias_contribuidos: number;
  indicador_aposentadoria_especial: boolean;
  agente_nocivo: string | null;
  grau_deficiencia: string | null;
  total_remuneracoes: number | null;
  quantidade_remuneracoes: number | null;
  periodo_valido: boolean;
  motivo_invalidacao: string | null;
}

export interface CNIS {
  id: string;
  tenant_id: string;
  cliente_id: string;
  nis: string;
  data_nascimento: string;
  periodo_inicial_cn: string | null;
  periodo_final_cn: string | null;
  tempo_contribuicao_total_dias: number | null;
  tempo_contribuicao_anos: number | null;
  total_contribuicoes: number | null;
  maior_salario_contribuicao: number | null;
  media_salarios_contribuicao: number | null;
  status_processamento: StatusProcessamento;
  erros_validacao: Record<string, unknown> | null;
  created_at: string;
}

export interface InconsistenciaItem {
  tipo: string;
  descricao: string;
  periodo_afetado: string | null;
  impacto_financeiro: number | null;
  recomendacao: string | null;
}

export interface AnaliseInconsistencias {
  cnis_id: string;
  total_inconsistencias: number;
  inconsistencias: InconsistenciaItem[];
  periodos_sobrepostos: Array<{ tipo: string; descricao: string; periodo: string }>;
  salarios_suspeitos: Array<{ tipo: string; descricao: string; periodo: string }>;
  periodos_sem_remuneracao: unknown[];
}

export interface CalculoRMI {
  id: string;
  tenant_id: string;
  cnis_id: string;
  cliente_id: string;
  nome_calculo: string;
  tipo_beneficio: TipoBeneficio;
  regra_aplicada: string | null;
  data_der: string;
  idade_na_der: number;
  tempo_contribuicao_na_der: number;
  salario_beneficio: number;
  coeficiente_calculo: number;
  fator_previdenciario: number | null;
  rmi_calculada: number;
  rmi_teto: number | null;
  rmi_final: number;
  detalhamento_calculo: {
    passo_a_passo: string[];
    total_salarios_analisados: number;
    salario_beneficio: number;
    coeficiente_aplicado: number;
    fator_previdenciario: number | null;
    [key: string]: unknown;
  };
  requisitos_atendidos: Record<string, unknown> | null;
  rmi_regra_anterior: number | null;
  diferenca_reforma: number | null;
  calculo_valido: boolean;
  alertas: string[] | null;
  erros: string[] | null;
  versao_calculo: string | null;
  created_at: string;
}

export interface CalculoRMIRequest {
  cnis_id: string;
  tipo_beneficio: TipoBeneficio;
  data_der: string;
  nome_calculo: string;
  regra_aplicada?: string;
}

export interface Simulacao {
  id: string;
  cnis_id: string;
  nome_simulacao: string | null;
  data_simulacao_futura: string;
  taxa_crescimento_salario: number | null;
  taxa_inflacao_anual: number | null;
  idade_na_data: number | null;
  tempo_contribuicao_projetado: number | null;
  salario_beneficio_projetado: number | null;
  rmi_projetada: number | null;
  rmi_valor_atual: number | null;
  created_at: string;
}

export interface SimulacaoRequest {
  cnis_id: string;
  nome_simulacao?: string;
  data_simulacao_futura: string;
  taxa_crescimento_salario: number;
  taxa_inflacao_anual: number;
}

export type TipoRemuneracao =
  | "salario"
  | "13o_salario"
  | "ferias"
  | "rescisao"
  | "adicional_noturno"
  | "hora_extra"
  | "comissao"
  | "gratificacao"
  | "outros";

export const TIPOS_REMUNERACAO: Record<TipoRemuneracao, string> = {
  salario: "Salário",
  "13o_salario": "13º Salário",
  ferias: "Férias",
  rescisao: "Rescisão",
  adicional_noturno: "Adicional Noturno",
  hora_extra: "Hora Extra",
  comissao: "Comissão",
  gratificacao: "Gratificação",
  outros: "Outros",
};

export interface RemuneracaoItem {
  id: string;
  cnis_id: string;
  mes_referencia: string;
  ano: number;
  mes: number;
  salario_contribuicao: number;
  salario_contribuicao_corrigido: number | null;
  teto_inss: number | null;
  tipo_remuneracao: TipoRemuneracao | null;
  contribuiu_inss: boolean;
  salario_valido: boolean;
  acima_teto: boolean;
  abaixo_minimo: boolean;
}

export interface RemuneracoesListResponse {
  items: RemuneracaoItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface RemuneracaoCreateRequest {
  competencia: string;
  salario_contribuicao: number;
  tipo_remuneracao: TipoRemuneracao;
  contribuiu_inss: boolean;
}

export interface ImportacaoCSVResult {
  criadas: number;
  ignoradas: number;
  erros: string[];
}
