/**
 * useVideos — React hook for video data and generation.
 *
 * Includes useVideoStatus for polling generation progress.
 *
 * Implementation: Phase 8.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { videosApi, type GenerateVideoPayload } from "@/lib/videos-api";

export const VIDEO_QUERY_KEYS = {
  all: ["videos"] as const,
  byProject: (projectId: string) => ["videos", "project", projectId] as const,
  detail: (id: string) => ["videos", "detail", id] as const,
  status: (id: string) => ["videos", "status", id] as const,
};

export function useVideos(projectId: string, page = 1) {
  return useQuery({
    queryKey: VIDEO_QUERY_KEYS.byProject(projectId),
    queryFn: () => videosApi.list(projectId, page),
    enabled: !!projectId,
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: VIDEO_QUERY_KEYS.detail(id),
    queryFn: () => videosApi.getById(id),
    enabled: !!id,
  });
}

export function useVideoStatus(id: string, enabled = true) {
  /**
   * Poll video generation status every 3 seconds.
   *
   * WHY refetchInterval?
   *   Celery processes take 1-30 minutes. We poll the lightweight
   *   /status endpoint instead of the full video endpoint to minimize
   *   payload size during the polling phase.
   */
  return useQuery({
    queryKey: VIDEO_QUERY_KEYS.status(id),
    queryFn: () => videosApi.getStatus(id),
    enabled: enabled && !!id,
    refetchInterval: (data) => {
      const status = data?.status;
      if (status === "completed" || status === "failed") return false;
      return 3000; // Poll every 3 seconds while in progress
    },
  });
}

export function useGenerateVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GenerateVideoPayload) => videosApi.generate(payload),
    onSuccess: (video) => {
      queryClient.invalidateQueries({
        queryKey: VIDEO_QUERY_KEYS.byProject(video.project_id),
      });
    },
  });
}
