import axios, { AxiosError } from "axios";
import { storage } from "@/utils/storage";
import type { TokenResponse } from "@/types/auth";

export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Injeta o Bearer token em todas as requisições.
api.interceptors.request.use((config) => {
  const token = storage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

// Trata 401: tenta renovar o access token via refresh token uma vez.
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status !== 401 || original?._retry) {
      return Promise.reject(error);
    }

    const refreshToken = storage.getRefreshToken();
    if (!refreshToken) {
      storage.clearTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        original!.headers!.Authorization = `Bearer ${token}`;
        return api(original!);
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post<TokenResponse>("/api/v1/auth/refresh", {
        refresh_token: refreshToken,
      });
      storage.setAccessToken(data.access_token);
      storage.setRefreshToken(data.refresh_token);
      processQueue(null, data.access_token);
      original!.headers!.Authorization = `Bearer ${data.access_token}`;
      return api(original!);
    } catch (refreshError) {
      processQueue(refreshError, null);
      storage.clearTokens();
      // Redireciona apenas se não estiver na inicialização do app.
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
