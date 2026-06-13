import { api } from "@/services/api";
import type { Client, ClientListResponse, ViaCepResponse } from "@/types/client";

export const clientsService = {
  list: (params?: { skip?: number; limit?: number; search?: string }) =>
    api.get<ClientListResponse>("/clients", { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<Client>(`/clients/${id}`).then((r) => r.data),

  create: (data: unknown) =>
    api.post<Client>("/clients", data).then((r) => r.data),

  update: (id: string, data: unknown) =>
    api.patch<Client>(`/clients/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/clients/${id}`),
};

export async function fetchCep(cep: string): Promise<ViaCepResponse | null> {
  const clean = cep.replace(/\D/g, "");
  if (clean.length !== 8) return null;
  try {
    const res = await fetch(`https://viacep.com.br/ws/${clean}/json/`);
    const data: ViaCepResponse = await res.json();
    return data.erro ? null : data;
  } catch {
    return null;
  }
}
