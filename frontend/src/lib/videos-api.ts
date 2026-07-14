/**
 * Videos API Service Layer.
 *
 * All functions: Implementation Phase 8.
 */

import apiClient from "@/lib/api-client";
import type { ApiPaginatedResponse, ApiSuccessResponse } from "@/types";
import type { Video, VideoStatus } from "@/types/models";

export interface GenerateVideoPayload {
  project_id: string;
  prompt: string;
  negative_prompt?: string;
  num_frames?: number;
  frame_duration_seconds?: number;
  transition?: string;
  include_narration?: boolean;
  voice_id?: string;
  fps?: number;
  width?: number;
  height?: number;
}

export const videosApi = {
  generate: async (payload: GenerateVideoPayload): Promise<Video> => {
    const { data } = await apiClient.post<ApiSuccessResponse<Video>>(
      "/videos/generate",
      payload,
    );
    return data.data;
  },

  list: async (projectId: string, page = 1, pageSize = 20): Promise<ApiPaginatedResponse<Video>> => {
    const { data } = await apiClient.get<ApiPaginatedResponse<Video>>(
      "/videos/",
      { params: { project_id: projectId, page, page_size: pageSize } },
    );
    return data;
  },

  getById: async (id: string): Promise<Video> => {
    const { data } = await apiClient.get<ApiSuccessResponse<Video>>(`/videos/${id}`);
    return data.data;
  },

  getStatus: async (id: string): Promise<VideoStatus> => {
    const { data } = await apiClient.get<ApiSuccessResponse<VideoStatus>>(
      `/videos/${id}/status`,
    );
    return data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/videos/${id}`);
  },
};
