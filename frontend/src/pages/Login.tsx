import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Scale, Eye, EyeOff, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";

const loginSchema = z.object({
  email: z.string().email("E-mail inválido."),
  password: z.string().min(1, "Informe a senha."),
});

type LoginForm = z.infer<typeof loginSchema>;

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginForm) => {
    setServerError(null);
    try {
      await login(data);
      navigate("/");
    } catch {
      setServerError("Credenciais inválidas. Verifique e tente novamente.");
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Painel esquerdo — ilustração/brand */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-slate-900 p-12">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600">
            <Scale size={18} className="text-white" />
          </div>
          <span className="text-lg font-bold text-white">Juprev</span>
        </div>

        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800 px-4 py-1.5">
              <ShieldCheck size={14} className="text-indigo-400" />
              <span className="text-xs text-slate-400">Plataforma segura · LGPD compliance</span>
            </div>
            <h2 className="text-4xl font-bold text-white leading-tight">
              Gestão previdenciária{" "}
              <span className="text-indigo-400">inteligente</span>{" "}
              para escritórios modernos.
            </h2>
            <p className="mt-4 text-slate-400 text-base leading-relaxed">
              Controle processos, calcule RMI, gerencie prazos e mantenha
              seus clientes informados — tudo em um só lugar.
            </p>
          </motion.div>

          <div className="mt-12 grid grid-cols-3 gap-6">
            {[
              { value: "100%", label: "Multi-tenant" },
              { value: "LGPD", label: "Compliance" },
              { value: "JWT", label: "Segurança" },
            ].map((s) => (
              <div key={s.label}>
                <p className="text-2xl font-bold text-white">{s.value}</p>
                <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-slate-600">
          © {new Date().getFullYear()} Juprev · Todos os direitos reservados
        </p>
      </div>

      {/* Painel direito — formulário */}
      <div className="flex flex-1 items-center justify-center bg-slate-50 px-6 py-12">
        <motion.div
          className="w-full max-w-sm"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Logo mobile */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
              <Scale size={15} className="text-white" />
            </div>
            <span className="font-bold text-slate-900">Juprev</span>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Entrar na conta
            </h1>
            <p className="mt-1.5 text-sm text-slate-500">
              Digite suas credenciais para acessar o sistema.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
            {/* Email */}
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-slate-700">
                E-mail
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="seu@email.com"
                {...register("email")}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
                className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 shadow-sm transition-all focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 aria-[invalid=true]:border-rose-400"
              />
              {errors.email && (
                <p id="email-error" className="mt-1.5 text-xs text-rose-600" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Senha */}
            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-slate-700">
                Senha
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  {...register("password")}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : undefined}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 pr-10 text-sm text-slate-900 placeholder-slate-400 shadow-sm transition-all focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 aria-[invalid=true]:border-rose-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {errors.password && (
                <p id="password-error" className="mt-1.5 text-xs text-rose-600" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Erro do servidor */}
            {serverError && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3" role="alert">
                <p className="text-sm text-rose-700">{serverError}</p>
              </div>
            )}

            <Button
              type="submit"
              loading={isSubmitting}
              className="w-full justify-center gap-2"
              size="lg"
            >
              {!isSubmitting && <ArrowRight size={15} />}
              {isSubmitting ? "Entrando..." : "Entrar"}
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-slate-400">
            Acesso restrito a usuários autorizados.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
