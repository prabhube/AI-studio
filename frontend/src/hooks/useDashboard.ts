/**
 * useDashboard — React hook for the aggregated dashboard summary.
 *
 * WHY a dedicated hook?
 *   Encapsulates the TanStack Query key, caching, and refetch policy for the
 *   dashboard home. Components call the hook — never the API directly.
 *
 * The dashboard is a "glanceable" surface: we keep it reasonably fresh with a
 * short stale time and a background refetch on window focus (inherited from the
 * global QueryClient defaults) so counts and activity stay current without a
 * manual reload.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/dashboard-api";

export const DASHBOARD_QUERY_KEYS = {
  all: ["dashboard"] as const,
  summary: () => ["dashboard", "summary"] as const,
};

export function useDashboardSummary() {
  return useQuery({
    queryKey: DASHBOARD_QUERY_KEYS.summary(),
    queryFn: () => dashboardApi.getSummary(),
    // Dashboard data is a lightweight aggregate — keep it fresh but not chatty.
    staleTime: 1000 * 30,
    // Don't hammer the backend if the endpoint is unavailable; surface the
    // empty/error state quickly and let the user retry via refetch-on-focus.
    retry: 1,
    placeholderData: (prev) => prev,
  });
}
