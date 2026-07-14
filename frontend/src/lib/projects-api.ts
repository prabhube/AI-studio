/**
 * Projects API Service Layer.
 *
 * WHY a dedicated service file per domain?
 *   Keeps HTTP concerns separate from React components and hooks.
 *   Components call hooks; hooks call API services; services call apiClient.
 *   Each layer has one responsibility.
 *
 * All functions: Implementation Phase 2.
 */

import apiClient from "@/lib/api-client";
import type {
  ApiPaginatedResponse,
  ApiSuccessResponse,
} from "@/types";
import type { Project } from "@/types/models";

export interface CreateProjectPayload {
  name: string;
  description?: string;
}

export interface UpdateProjectPayload {
  name?: string;
  description?: string;
}

export const projectsApi = {
  create: async (payload: CreateProjectPayload): Promise<Project> => {
    const { data } = await apiClient.post<ApiSuccessResponse<Project>>(
      "/projects/",
      payload,
    );
    return data.data;
  },

  list: async (page = 1, pageSize = 20): Promise<ApiPaginatedResponse<Project>> => {
    const { data } = await apiClient.get<ApiPaginatedResponse<Project>>(
      "/projects/",
      { params: { page, page_size: pageSize } },
    );
    return data;
  },

  getById: async (id: string): Promise<Project> => {
    const { data } = await apiClient.get<ApiSuccessResponse<Project>>(
      `/projects/${id}`,
    );
    return data.data;
  },

  update: async (id: string, payload: UpdateProjectPayload): Promise<Project> => {
    const { data } = await apiClient.patch<ApiSuccessResponse<Project>>(
      `/projects/${id}`,
      payload,
    );
    return data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },
};
