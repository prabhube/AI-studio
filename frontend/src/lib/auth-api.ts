/**
 * Authentication API service.
 *
 * Typed wrappers for all auth endpoints. Components and hooks import
 * from here rather than calling apiClient directly.
 */

import { apiGet, apiPost, ApiResponse } from "@/lib/api-client";
import type { AuthUser } from "@/store/auth-store";

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AccessTokenOnly {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface GoogleOAuthUrl {
  url: string;
  state: string;
}

// ---------------------------------------------------------------------------
// Request types
// ---------------------------------------------------------------------------

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface PasswordChangePayload {
  current_password: string;
  new_password: string;
}

export interface GoogleCallbackPayload {
  code: string;
  state: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const authApi = {
  /** Register a new account. Returns the created user (not tokens). */
  async register(payload: RegisterPayload): Promise<AuthUser> {
    const response = await apiPost<ApiResponse<AuthUser>>("/auth/register", payload);
    return response.data;
  },

  /** Login with email + password. Returns a token pair. */
  async login(payload: LoginPayload): Promise<TokenPair> {
    const response = await apiPost<ApiResponse<TokenPair>>("/auth/login", payload);
    return response.data;
  },

  /**
   * Rotate the refresh token and get a new access token.
   * Returns the new access token and optionally a new refresh token.
   */
  async refresh(refreshToken: string): Promise<AccessTokenOnly> {
    const response = await apiPost<ApiResponse<AccessTokenOnly>>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /** Revoke both tokens. Access token is sent via Authorization header. */
  async logout(refreshToken: string): Promise<void> {
    await apiPost("/auth/logout", { refresh_token: refreshToken });
  },

  /** Get the currently authenticated user's profile. */
  async getMe(): Promise<AuthUser> {
    const response = await apiGet<ApiResponse<AuthUser>>("/auth/me");
    return response.data;
  },

  /** Change the current user's password. */
  async changePassword(payload: PasswordChangePayload): Promise<void> {
    await apiPost("/auth/change-password", payload);
  },

  /** Get the Google OAuth redirect URL. */
  async getGoogleOAuthUrl(): Promise<GoogleOAuthUrl> {
    const response = await apiGet<ApiResponse<GoogleOAuthUrl>>("/auth/google");
    return response.data;
  },

  /** Exchange the Google authorization code for JWT tokens. */
  async googleCallback(payload: GoogleCallbackPayload): Promise<TokenPair> {
    const response = await apiPost<ApiResponse<TokenPair>>(
      "/auth/google/callback",
      payload
    );
    return response.data;
  },
};
