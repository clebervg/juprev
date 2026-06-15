import { api } from "@/services/api";
import type {
  AnaliseInconsistencias,
  CalculoRMI,
  CalculoRMIRequest,
  CNIS,
  CNISListResponse,
  ImportacaoCSVResult,
  RemuneracaoCreateRequest,
  RemuneracaoItem,
  RemuneracoesListResponse,
  Simulacao,
  SimulacaoRequest,
} from "@/types/cnis";

export const cnisService = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<CNISListResponse>("/cnis", { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<CNIS>(`/cnis/${id}`).then((r) => r.data),

  create: (data: {
    cliente_id: string;
    nome_segurado: string;
    cpf: string;
    nis?: string | null;
    data_nascimento: string;
    arquivo_original_nome?: string;
  }) => api.post<CNIS>("/cnis", data).then((r) => r.data),

  delete: (id: string) => api.delete(`/cnis/${id}`),

  // Cálculos
  calcular: (cnisId: string, data: CalculoRMIRequest, params: {
    genero?: string;
    data_nascimento?: string;
    tempo_especial_dias?: number;
    grau_deficiencia?: string;
  }) =>
    api.post<CalculoRMI>(`/cnis/${cnisId}/calculos`, data, { params }).then((r) => r.data),

  listarCalculos: (cnisId: string) =>
    api.get<CalculoRMI[]>(`/cnis/${cnisId}/calculos`).then((r) => r.data),

  // Inconsistências
  analisarInconsistencias: (cnisId: string) =>
    api.get<AnaliseInconsistencias>(`/cnis/${cnisId}/inconsistencias`).then((r) => r.data),

  // Simulações
  simular: (cnisId: string, data: SimulacaoRequest, params: { genero?: string }) =>
    api.post<Simulacao>(`/cnis/${cnisId}/simulacoes`, data, { params }).then((r) => r.data),

  // Remunerações
  listarRemuneracoes: (cnisId: string, params?: { skip?: number; limit?: number }) =>
    api.get<RemuneracoesListResponse>(`/cnis/${cnisId}/remuneracoes`, { params }).then((r) => r.data),

  criarRemuneracao: (cnisId: string, data: RemuneracaoCreateRequest) =>
    api.post<RemuneracaoItem>(`/cnis/${cnisId}/remuneracoes`, data).then((r) => r.data),

  editarRemuneracao: (cnisId: string, remId: string, data: Partial<RemuneracaoCreateRequest>) =>
    api.patch<RemuneracaoItem>(`/cnis/${cnisId}/remuneracoes/${remId}`, data).then((r) => r.data),

  deletarRemuneracao: (cnisId: string, remId: string) =>
    api.delete(`/cnis/${cnisId}/remuneracoes/${remId}`),

  importarCSV: (cnisId: string, file: File) => {
    const form = new FormData();
    form.append("arquivo", file);
    return api.post<ImportacaoCSVResult>(`/cnis/${cnisId}/remuneracoes/importar-csv`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  processarPDF: (cnisId: string, file: File) => {
    const form = new FormData();
    form.append("arquivo", file);
    return api.post<ImportacaoCSVResult>(`/cnis/${cnisId}/processar-pdf`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    }).then((r) => r.data);
  },

  corrigirRemuneracoes: (cnisId: string) =>
    api.post<{ ok: boolean }>(`/cnis/${cnisId}/remuneracoes/corrigir`).then((r) => r.data),
};
