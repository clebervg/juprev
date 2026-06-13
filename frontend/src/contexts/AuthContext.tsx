import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/services/api";
import { storage } from "@/utils/storage";
import type { AuthUser, LoginPayload, TokenResponse } from "@/types/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Ao montar, tenta restaurar a sessão a partir dos tokens salvos.
  useEffect(() => {
    const restore = async () => {
      const accessToken = storage.getAccessToken();
      const refreshToken = storage.getRefreshToken();

      if (!accessToken && !refreshToken) {
        setIsLoading(false);
        return;
      }

      try {
        // Tenta buscar o usuário com o access token atual.
        const { data } = await api.get<AuthUser>("/users/me");
        setUser(data);
      } catch {
        // Se falhar (401), o interceptor do Axios já vai tentar o refresh.
        // Se o refresh também falhar, o interceptor limpa os tokens e redireciona.
        // Aqui chegamos apenas se ambos falharam.
        storage.clearTokens();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    restore();
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const { data } = await api.post<TokenResponse>("/auth/login", payload);
    storage.setAccessToken(data.access_token);
    storage.setRefreshToken(data.refresh_token);

    const { data: me } = await api.get<AuthUser>("/users/me");
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    storage.clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  return ctx;
}
