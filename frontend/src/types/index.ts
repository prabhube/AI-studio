/**
 * Shared TypeScript types used across the frontend application.
 */

// ============================================================
// API Response Envelopes
// ============================================================

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

export interface ApiErrorResponse {
  success: false;
  error: string;
  details?: Array<{ field?: string; message: string }>;
  request_id?: string;
}

export interface ApiPaginatedResponse<T> {
  success: true;
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================
// Authentication
// ============================================================

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

// ============================================================
// User
// ============================================================

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Health
// ============================================================

export interface HealthStatus {
  status: "ok" | "degraded";
  version: string;
  environment: string;
  services: Record<string, string>;
}
