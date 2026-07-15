/**
 * Dashboard Domain Types.
 *
 * WHY a separate dashboard.ts?
 *   The dashboard aggregates data from several domains (projects, videos,
 *   storage, billing) into a single read-optimised summary payload. These
 *   shapes don't belong to any one domain in models.ts, so they live here.
 *
 *   The backend exposes this as `GET /dashboard/summary` returning a single
 *   ApiSuccessResponse<DashboardSummary> so the home page renders with one
 *   round-trip instead of N per-domain requests.
 */

import type { Project, Video } from "@/types/models";

// ============================================================
// Aggregate counters
// ============================================================

export interface DashboardStats {
  projects: number;
  videos: number;
  images: number;
  audio_clips: number;
  /** Optional week-over-week deltas, shown as trend indicators. */
  deltas?: {
    projects?: number;
    videos?: number;
    images?: number;
    audio_clips?: number;
  };
}

// ============================================================
// Credits / billing
// ============================================================

export interface CreditsBalance {
  /** Credits currently available to spend. */
  balance: number;
  /** Credits included with the plan each billing cycle. */
  monthly_allowance: number;
  /** Credits consumed in the current billing cycle. */
  used_this_month: number;
  /** Human-readable plan name, e.g. "Free", "Pro", "Studio". */
  plan: string;
  /** ISO timestamp of the next allowance renewal, or null for one-off credits. */
  renews_at: string | null;
}

// ============================================================
// Storage usage
// ============================================================

export interface StorageBreakdown {
  videos: number;
  images: number;
  audio: number;
  other: number;
}

export interface StorageUsage {
  /** Bytes consumed by this user's media. */
  used_bytes: number;
  /** Total quota in bytes. */
  total_bytes: number;
  /** Per-media-type breakdown in bytes. */
  by_type: StorageBreakdown;
}

// ============================================================
// Activity timeline
// ============================================================

export type ActivityType =
  | "project_created"
  | "video_generated"
  | "video_failed"
  | "image_generated"
  | "audio_generated"
  | "credits_purchased"
  | "credits_spent";

export interface ActivityEvent {
  id: string;
  type: ActivityType;
  title: string;
  description: string | null;
  /** Optional link target (e.g. the project or video detail page). */
  href: string | null;
  created_at: string;
}

// ============================================================
// Aggregate summary
// ============================================================

export interface DashboardSummary {
  stats: DashboardStats;
  credits: CreditsBalance;
  storage: StorageUsage;
  recent_projects: Project[];
  recent_videos: Video[];
  activity: ActivityEvent[];
}
