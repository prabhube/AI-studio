/**
 * Dashboard API Service Layer.
 *
 * WHY a dedicated service file?
 *   Keeps HTTP concerns separate from React components and hooks.
 *   Components call hooks; hooks call this service; this service calls
 *   apiClient. Each layer has one responsibility.
 *
 * Endpoint contract (backend: Phase 2+):
 *   GET /dashboard/summary
 *     → ApiSuccessResponse<DashboardSummary>
 *
 *   A single aggregated read so the dashboard home renders in one round-trip.
 */

import apiClient from "@/lib/api-client";
import type { ApiSuccessResponse } from "@/types";
import type { DashboardSummary } from "@/types/dashboard";

export const dashboardApi = {
  /** Fetch the aggregated dashboard summary for the current user. */
  getSummary: async (): Promise<DashboardSummary> => {
    const { data } = await apiClient.get<ApiSuccessResponse<DashboardSummary>>(
      "/dashboard/summary",
    );
    return data.data;
  },
};
