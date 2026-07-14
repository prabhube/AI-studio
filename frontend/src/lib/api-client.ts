/**
 * Centralized Axios API client.
 *
 * Design decisions:
 *  - Auth token injection: the request interceptor reads the current access
 *    token from the Zustand auth store on every request. No token caching
 *    in this module — the store is the single source of truth.
 *  - 401 refresh flow: when a request returns 401, the response interceptor
 *    silently refreshes the access token using the stored refresh token,
 *    then retries the original request. All parallel requests that also
 *    fail with 401 are queued and replayed with the new token.
 *  - A request is never retried if _retry=true (already retried once) or
 *    if it is the refresh call itself (prevents infinite loops).
 *  - Non-401 5xx responses are retried up to 3 times with exponential
 *    backoff before the error is surfaced.
 *  - Every request gets a unique X-Request-ID for backend log correlation.
 *  - All HTTP errors are normalized into ApiError instances.
 */

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";

import { env } from "@/env";

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export interface ApiErrorDetail {
  field: string | null;
  message: string;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly details: ApiErrorDetail[] = [],
    public readonly requestId?: string
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isUnauthorized(): boolean { return this.status === 401; }
  get isForbidden(): boolean { return this.status === 403; }
  get isNotFound(): boolean { return this.status === 404; }
  get isConflict(): boolean { return this.status === 409; }
  get isValidationError(): boolean { return this.status === 422; }
  get isServerError(): boolean { return this.status >= 500; }
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedApiResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateRequestId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryable(status: number | undefined): boolean {
  if (!status) return true;  // network error
  return status >= 500;
}

function extractErrorMessage(data: unknown): string {
  if (typeof data === "object" && data !== null) {
    const d = data as Record<string, unknown>;
    if (typeof d.error === "string") return d.error;
    if (typeof d.detail === "string") return d.detail;
    if (typeof d.message === "string") return d.message;
  }
  return "An unexpected error occurred.";
}

function extractErrorDetails(data: unknown): ApiErrorDetail[] {
  if (typeof data === "object" && data !== null) {
    const d = data as Record<string, unknown>;
    if (Array.isArray(d.details)) return d.details as ApiErrorDetail[];
  }
  return [];
}

function extractRequestId(headers: Record<string, string>): string | undefined {
  return headers["x-request-id"] ?? headers["X-Request-ID"];
}

// ---------------------------------------------------------------------------
// Refresh token queue (prevents cascading 401s during token refresh)
// ---------------------------------------------------------------------------

let isRefreshing = false;
let refreshQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function drainQueue(error: unknown, token: string | null = null): void {
  refreshQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  refreshQueue = [];
}

// ---------------------------------------------------------------------------
// Instance factory
// ---------------------------------------------------------------------------

function createApiClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: env.apiUrl,
    timeout: env.apiTimeoutMs,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  // ------------------------------------------------------------------
  // Request interceptor — inject X-Request-ID and Authorization header
  // ------------------------------------------------------------------
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      config.headers["X-Request-ID"] = generateRequestId();

      // Lazy import to avoid circular dependency (auth-store imports api-client)
      try {
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const { useAuthStore } = require("@/store/auth-store");
        const accessToken = useAuthStore.getState().tokens?.accessToken;
        if (accessToken) {
          config.headers["Authorization"] = `Bearer ${accessToken}`;
        }
      } catch {
        // Store not available (e.g. SSR or before hydration)
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  // ------------------------------------------------------------------
  // Response interceptor — retry on 5xx, handle 401 with token refresh
  // ------------------------------------------------------------------
  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const config = error.config as AxiosRequestConfig & {
        _retryCount?: number;
        _retry?: boolean;
      };

      // --- 401: attempt token refresh ---
      if (
        error.response?.status === 401 &&
        !config._retry &&
        !config.url?.includes("/auth/refresh") &&
        !config.url?.includes("/auth/login")
      ) {
        config._retry = true;

        if (isRefreshing) {
          // Queue this request until the refresh completes
          return new Promise<string>((resolve, reject) => {
            refreshQueue.push({ resolve, reject });
          }).then((newToken) => {
            if (config.headers) {
              config.headers["Authorization"] = `Bearer ${newToken}`;
            }
            return instance(config);
          });
        }

        isRefreshing = true;

        try {
          // eslint-disable-next-line @typescript-eslint/no-require-imports
          const { useAuthStore } = require("@/store/auth-store");
          const state = useAuthStore.getState();
          const refreshToken = state.tokens?.refreshToken;

          if (!refreshToken) {
            drainQueue(error);
            state.clearAuth();
            if (typeof window !== "undefined") {
              window.location.href = "/login";
            }
            return Promise.reject(error);
          }

          // Call refresh endpoint directly (avoid interceptor loop)
          const refreshResp = await axios.post(
            `${env.apiUrl}/auth/refresh`,
            { refresh_token: refreshToken },
            { headers: { "Content-Type": "application/json" } }
          );

          const newAccessToken: string = refreshResp.data.data.access_token;
          const expiresIn: number = refreshResp.data.data.expires_in ?? 3600;

          state.updateAccessToken(newAccessToken, expiresIn);
          drainQueue(null, newAccessToken);

          if (config.headers) {
            config.headers["Authorization"] = `Bearer ${newAccessToken}`;
          }

          return instance(config);
        } catch (refreshError) {
          drainQueue(refreshError);
          // eslint-disable-next-line @typescript-eslint/no-require-imports
          const { useAuthStore } = require("@/store/auth-store");
          useAuthStore.getState().clearAuth();
          if (typeof window !== "undefined") {
            window.location.href = "/login?session_expired=1";
          }
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      // --- 5xx: exponential backoff retry ---
      const maxRetries = 3;
      const retryCount = config._retryCount ?? 0;

      if (retryCount < maxRetries && isRetryable(error.response?.status) && config) {
        config._retryCount = retryCount + 1;
        await sleep(500 * Math.pow(2, retryCount));
        return instance(config);
      }

      // --- Normalize to ApiError ---
      const status = error.response?.status ?? 0;
      const responseData = error.response?.data;
      const responseHeaders = (error.response?.headers ?? {}) as Record<string, string>;

      if (error.response) {
        throw new ApiError(
          status,
          extractErrorMessage(responseData),
          extractErrorDetails(responseData),
          extractRequestId(responseHeaders)
        );
      }

      if (error.code === "ECONNABORTED") {
        throw new ApiError(0, "Request timed out. Please try again.");
      }

      throw new ApiError(0, "Network error. Check your connection and try again.");
    }
  );

  return instance;
}

const apiClient: AxiosInstance = createApiClient();
export default apiClient;

// ---------------------------------------------------------------------------
// Typed convenience wrappers
// ---------------------------------------------------------------------------

export async function apiGet<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
  const r = await apiClient.get<T>(path, config);
  return r.data;
}

export async function apiPost<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const r = await apiClient.post<T>(path, body, config);
  return r.data;
}

export async function apiPatch<T>(path: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const r = await apiClient.patch<T>(path, body, config);
  return r.data;
}

export async function apiDelete<T = void>(path: string, config?: AxiosRequestConfig): Promise<T> {
  const r = await apiClient.delete<T>(path, config);
  return r.data;
}
