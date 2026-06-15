import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  UserPlus, Search, Eye, Trash2, Users,
  ChevronsLeft, ChevronLeft, ChevronRight, ChevronsRight,
} from "lucide-react";
import { toast } from "sonner";
import { clientsService } from "@/services/clients";
import { PageTransition } from "@/components/ui/PageTransition";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SkeletonTable } from "@/components/ui/Skeleton";
import type { ClientListItem } from "@/types/client";

const LIMIT = 20;

export function ClientesPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);

  // Debounce: reseta para página 0 e dispara query 350ms após parar de digitar
  useEffect(() => {
    const t = setTimeout(() => {
      setSearch(searchInput);
      setPage(0);
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["clients", search, page],
    queryFn: () => clientsService.list({ skip: page * LIMIT, limit: LIMIT, search: search || undefined }),
    placeholderData: (prev) => prev,
  });

  // Pré-carrega a próxima página
  useEffect(() => {
    if (!data) return;
    const totalPages = Math.ceil(data.total / LIMIT);
    if (page + 1 < totalPages) {
      qc.prefetchQuery({
        queryKey: ["clients", search, page + 1],
        queryFn: () => clientsService.list({ skip: (page + 1) * LIMIT, limit: LIMIT, search: search || undefined }),
      });
    }
  }, [data, page, search, qc]);

  const handleDelete = async (id: string, nome: string) => {
    if (!confirm(`Deseja excluir o cliente "${nome}"? Esta ação não pode ser desfeita.`)) return;
    try {
      await clientsService.delete(id);
      toast.success("Cliente excluído com sucesso.");
      qc.invalidateQueries({ queryKey: ["clients"] });
    } catch {
      toast.error("Erro ao excluir cliente.");
    }
  };

  const formatDate = (iso: string) => new Date(iso).toLocaleDateString("pt-BR");

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));
  const from = total === 0 ? 0 : page * LIMIT + 1;
  const to = Math.min((page + 1) * LIMIT, total);

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
              {data
                ? `${total} cliente${total !== 1 ? "s" : ""} cadastrado${total !== 1 ? "s" : ""}`
                : "Carregando..."}
            </p>
          </div>
          <Button onClick={() => navigate("/clientes/novo")}>
            <UserPlus size={15} />
            Novo Cliente
          </Button>
        </div>

        {/* Busca */}
        <div className="relative max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por nome ou CPF..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 pl-9 pr-3 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
          {isFetching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          )}
        </div>

        {/* Tabela */}
        {isLoading ? (
          <SkeletonTable rows={LIMIT} />
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

            {/* Paginação */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between gap-4 px-6 py-3 border-t border-slate-100 dark:border-slate-700">
                <p className="text-xs text-slate-400 tabular-nums shrink-0">
                  {from}–{to} de {total}
                </p>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage(0)}
                    disabled={page === 0}
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    aria-label="Primeira página"
                  >
                    <ChevronsLeft size={15} />
                  </button>
                  <button
                    onClick={() => setPage((p) => p - 1)}
                    disabled={page === 0}
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    aria-label="Página anterior"
                  >
                    <ChevronLeft size={15} />
                  </button>
                  <span className="flex h-8 min-w-[2.5rem] items-center justify-center rounded-lg bg-indigo-600 px-2.5 text-xs font-semibold text-white tabular-nums">
                    {page + 1}<span className="mx-1 opacity-60">/</span>{totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= totalPages - 1}
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    aria-label="Próxima página"
                  >
                    <ChevronRight size={15} />
                  </button>
                  <button
                    onClick={() => setPage(totalPages - 1)}
                    disabled={page >= totalPages - 1}
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                    aria-label="Última página"
                  >
                    <ChevronsRight size={15} />
                  </button>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </PageTransition>
  );
}
