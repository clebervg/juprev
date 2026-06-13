import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { UserPlus, Search, Eye, Trash2, Users } from "lucide-react";
import { toast } from "sonner";
import { clientsService } from "@/services/clients";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SkeletonTable } from "@/components/ui/Skeleton";
import type { ClientListItem } from "@/types/client";

export function ClientesPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["clients", search],
    queryFn: () => clientsService.list({ search: search || undefined }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
  };

  const handleDelete = async (id: string, nome: string) => {
    if (!confirm(`Deseja excluir o cliente "${nome}"? Esta ação não pode ser desfeita.`)) return;
    try {
      await clientsService.delete(id);
      toast.success("Cliente excluído com sucesso.");
    } catch {
      toast.error("Erro ao excluir cliente.");
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("pt-BR");

  return (
    <PageTransition>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Clientes
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {data ? `${data.total} cliente${data.total !== 1 ? "s" : ""} cadastrado${data.total !== 1 ? "s" : ""}` : "Carregando..."}
            </p>
          </div>
          <Button onClick={() => navigate("/clientes/novo")}>
            <UserPlus size={15} />
            Novo Cliente
          </Button>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-sm">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por nome..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 pl-9 pr-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <Button type="submit" variant="secondary" size="md">
            Buscar
          </Button>
        </form>

        {/* Tabela */}
        {isLoading ? (
          <SkeletonTable rows={6} />
        ) : data?.items.length === 0 ? (
          <Card className="py-20 flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-slate-50 dark:bg-slate-700 mb-4">
              <Users size={24} className="text-slate-300 dark:text-slate-500" />
            </div>
            <p className="font-medium text-slate-600 dark:text-slate-300">Nenhum cliente encontrado</p>
            <p className="mt-1 text-sm text-slate-400">
              {search ? "Tente uma busca diferente." : "Cadastre o primeiro cliente."}
            </p>
            {!search && (
              <Button className="mt-4" onClick={() => navigate("/clientes/novo")}>
                <UserPlus size={14} /> Novo Cliente
              </Button>
            )}
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm" aria-label="Lista de clientes">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Nome
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      CPF
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 hidden md:table-cell">
                      Telefone
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 hidden lg:table-cell">
                      Cidade / UF
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 hidden lg:table-cell">
                      Cadastro
                    </th>
                    <th className="px-6 py-4 w-24" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {data?.items.map((client: ClientListItem) => (
                    <motion.tr
                      key={client.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="group hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="px-6 py-4 font-medium text-slate-800 dark:text-slate-200">
                        {client.nome}
                      </td>
                      <td className="px-6 py-4 text-slate-500 dark:text-slate-400 font-mono text-xs">
                        {client.cpf_mascarado}
                      </td>
                      <td className="px-6 py-4 text-slate-500 dark:text-slate-400 hidden md:table-cell">
                        {client.telefone_celular ?? "—"}
                      </td>
                      <td className="px-6 py-4 text-slate-500 dark:text-slate-400 hidden lg:table-cell">
                        {client.cidade && client.uf ? `${client.cidade} / ${client.uf}` : "—"}
                      </td>
                      <td className="px-6 py-4 text-slate-400 dark:text-slate-500 text-xs hidden lg:table-cell">
                        {formatDate(client.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => navigate(`/clientes/${client.id}`)}
                            className="rounded-md p-1.5 text-slate-400 hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-950 transition-colors"
                            aria-label="Ver detalhes"
                          >
                            <Eye size={15} />
                          </button>
                          <button
                            onClick={() => handleDelete(client.id, client.nome)}
                            className="rounded-md p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950 transition-colors"
                            aria-label="Excluir cliente"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </PageTransition>
  );
}
