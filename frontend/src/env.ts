/**
 * Typed, validated environment configuration.
 *
 * Design decisions:
 *  - All environment variable access goes through this module.
 *    No component or hook reads process.env directly.
 *  - Variables are validated at module-load time with clear error messages,
 *    so misconfiguration fails loudly at startup instead of silently at runtime.
 *  - NEXT_PUBLIC_* variables are safe to use client-side.
 *    Server-only variables (without NEXT_PUBLIC_) must never be used in
 *    client components.
 *  - Default values are provided for all optional settings so the app works
 *    out of the box after cloning without configuring .env.local.
 */

function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(
      `Missing required environment variable: ${key}\n` +
        `Add it to .env.local or your deployment environment.`
    );
  }
  return value;
}

function optionalEnv(key: string, fallback: string): string {
  return process.env[key] ?? fallback;
}

function optionalBoolEnv(key: string, fallback: boolean): boolean {
  const v = process.env[key];
  if (v === undefined) return fallback;
  return v === "true" || v === "1";
}

function optionalIntEnv(key: string, fallback: number): number {
  const v = process.env[key];
  if (v === undefined) return fallback;
  const parsed = parseInt(v, 10);
  if (isNaN(parsed)) return fallback;
  return parsed;
}

// ---------------------------------------------------------------------------
// Public client-side environment (NEXT_PUBLIC_* only)
// ---------------------------------------------------------------------------

export const env = {
  /** Base URL for the FastAPI backend. Requests are prefixed with /api/v1. */
  apiUrl: optionalEnv(
    "NEXT_PUBLIC_API_URL",
    "http://localhost:8000/api/v1"
  ),

  /** Application name shown in the browser tab and metadata. */
  appName: optionalEnv("NEXT_PUBLIC_APP_NAME", "Prabhu AI Studio"),

  /** Application version, injected at build time. */
  appVersion: optionalEnv("NEXT_PUBLIC_APP_VERSION", "1.0.0"),

  /** Deployment environment. */
  nodeEnv: optionalEnv("NODE_ENV", "development") as
    | "development"
    | "production"
    | "test",

  /** Enable ReactQuery devtools (only in development by default). */
  showDevtools: optionalBoolEnv(
    "NEXT_PUBLIC_SHOW_DEVTOOLS",
    process.env.NODE_ENV === "development"
  ),

  /** Default API request timeout in milliseconds. */
  apiTimeoutMs: optionalIntEnv("NEXT_PUBLIC_API_TIMEOUT_MS", 30_000),

  /** How often to poll the /health endpoint (ms). 0 = disabled. */
  healthPollIntervalMs: optionalIntEnv(
    "NEXT_PUBLIC_HEALTH_POLL_INTERVAL_MS",
    30_000
  ),
} as const;

export const isDev = env.nodeEnv === "development";
export const isProd = env.nodeEnv === "production";
