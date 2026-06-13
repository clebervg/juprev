export type EstadoCivil = "solteiro" | "casado" | "divorciado" | "viuvo" | "uniao_estavel";
export type Genero = "masculino" | "feminino" | "outro";
export type Parentesco = "filho" | "conjuge" | "companheiro" | "outros";
export type TipoResidencia = "propria" | "alugada" | "cedida" | "outras";

export interface Dependente {
  id: string;
  nome: string;
  cpf: string | null;
  data_nascimento: string | null;
  parentesco: Parentesco | null;
  e_beneficiario: boolean;
  percentual_dependencia: number | null;
}

export interface Client {
  id: string;
  tenant_id: string;
  // Dados pessoais
  nome: string;
  cpf: string | null;
  rg: string | null;
  rg_orgao_expedidor: string | null;
  data_nascimento: string | null;
  nome_mae: string | null;
  nome_pai: string | null;
  estado_civil: EstadoCivil | null;
  genero: Genero | null;
  nis: string | null;
  ctps_numero: string | null;
  ctps_serie: string | null;
  escolaridade: string | null;
  profissao: string | null;
  tempo_contribuicao_anos: number | null;
  // Contato
  email: string | null;
  telefone_celular: string | null;
  whatsapp: boolean;
  telefone_fixo: string | null;
  contato_emergencia_nome: string | null;
  contato_emergencia_telefone: string | null;
  // Endereço
  cep: string | null;
  logradouro: string | null;
  numero: string | null;
  complemento: string | null;
  bairro: string | null;
  cidade: string | null;
  uf: string | null;
  tipo_residencia: TipoResidencia | null;
  // Dados adicionais
  renda_mensal: number | null;
  possui_deficiencia: boolean;
  tipo_deficiencia: string | null;
  observacoes: string | null;
  created_at: string;
  dependentes: Dependente[];
}

export interface ClientListItem {
  id: string;
  nome: string;
  cpf_mascarado: string;
  telefone_celular: string | null;
  cidade: string | null;
  uf: string | null;
  created_at: string;
}

export interface ClientListResponse {
  items: ClientListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface ViaCepResponse {
  cep: string;
  logradouro: string;
  bairro: string;
  localidade: string;
  uf: string;
  erro?: boolean;
}
