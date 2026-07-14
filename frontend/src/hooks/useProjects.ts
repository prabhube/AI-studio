/**
 * useProjects — React hook for project data management.
 *
 * WHY a dedicated hook per domain?
 *   Keeps TanStack Query keys, cache invalidation, and mutation
 *   logic encapsulated. Components call the hook — never the API directly.
 *
 * Implementation: Phase 2.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  projectsApi,
  type CreateProjectPayload,
  type UpdateProjectPayload,
} from "@/lib/projects-api";

export const PROJECT_QUERY_KEYS = {
  all: ["projects"] as const,
  list: (page: number) => ["projects", "list", page] as const,
  detail: (id: string) => ["projects", "detail", id] as const,
};

export function useProjects(page = 1) {
  return useQuery({
    queryKey: PROJECT_QUERY_KEYS.list(page),
    queryFn: () => projectsApi.list(page),
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: PROJECT_QUERY_KEYS.detail(id),
    queryFn: () => projectsApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProjectPayload) => projectsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECT_QUERY_KEYS.all });
    },
  });
}

export function useUpdateProject(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProjectPayload) => projectsApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECT_QUERY_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: PROJECT_QUERY_KEYS.all });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECT_QUERY_KEYS.all });
    },
  });
}
