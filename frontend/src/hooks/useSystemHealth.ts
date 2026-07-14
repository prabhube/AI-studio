/**
 * System health polling hook.
 *
 * Polls the backend /health endpoint at a configurable interval and
 * returns the overall status and per-service latencies.
 *
 * Used by the TopBar to show a live system status indicator.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api-client";
import { env } from "@/env";

// ---------------------------------------------------------------------------
// Types — mirrors backend HealthCheckResponse schema
// ---------------------------------------------------------------------------

export interface ServiceStatus {
  status: "ok" | "error" | "degraded";
  latency_ms: number | null;
  detail: string | null;
}

export interface HealthCheckResponse {
  status: "ok" | "degraded" | "unhealthy";
  version: string;
  environment: string;
  uptime_seconds: number;
  services: {
    postgres: ServiceStatus;
    redis: ServiceStatus;
  };
  disk?: {
    path: string;
    total_gb?: number;
    free_gb?: number;
    percent_used?: number;
    error?: string;
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useSystemHealth() {
  return useQuery<HealthCheckResponse>({
    queryKey: ["system", "health"],
    queryFn: () => apiGet<HealthCheckResponse>("/health"),
    // Poll at the configured interval (default 30s). If interval is 0, disable polling.
    refetchInterval: env.healthPollIntervalMs > 0 ? env.healthPollIntervalMs : false,
    // Don't retry on error — we want to show degraded state quickly
    retry: false,
    // Keep showing previous data while re-fetching
    placeholderData: (prev) => prev,
    // Never mark as stale — the refetchInterval drives freshness
    staleTime: env.healthPollIntervalMs,
  });
}

// ---------------------------------------------------------------------------
// Derived status helpers
// ---------------------------------------------------------------------------

export type HealthStatus = "healthy" | "degraded" | "unhealthy" | "unknown";

export function deriveOverallStatus(
  data: HealthCheckResponse | undefined,
  isError: boolean
): HealthStatus {
  if (isError) return "unhealthy";
  if (!data) return "unknown";
  if (data.status === "ok") return "healthy";
  if (data.status === "degraded") return "degraded";
  return "unhealthy";
}

export const STATUS_COLORS: Record<HealthStatus, string> = {
  healthy:   "bg-emerald-400",
  degraded:  "bg-amber-400",
  unhealthy: "bg-red-400",
  unknown:   "bg-white/20",
};

export const STATUS_LABELS: Record<HealthStatus, string> = {
  healthy:   "System Ready",
  degraded:  "Degraded",
  unhealthy: "Unavailable",
  unknown:   "Checking…",
};
