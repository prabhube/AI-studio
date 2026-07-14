/**
 * Domain Model TypeScript Interfaces.
 *
 * WHY a separate models.ts?
 *   api.ts contains API envelope types (SuccessResponse, etc.).
 *   models.ts contains the actual domain objects returned inside those envelopes.
 *   This separation mirrors the backend's schema design.
 */

// ============================================================
// Project
// ============================================================

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  thumbnail_url: string | null;
  status: "draft" | "generating" | "completed" | "failed";
  created_at: string;
  updated_at: string;
}

// ============================================================
// Video
// ============================================================

export interface Video {
  id: string;
  project_id: string;
  prompt: string;
  file_path: string | null;
  thumbnail_path: string | null;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  file_size_bytes: number | null;
  status: "pending" | "queued" | "generating" | "completed" | "failed";
  error_message: string | null;
  celery_task_id: string | null;
  generation_time_seconds: number | null;
  created_at: string;
  updated_at: string;
}

export interface VideoStatus {
  id: string;
  status: string;
  progress_percent: number | null;
  error_message: string | null;
}

// ============================================================
// Image
// ============================================================

export interface GeneratedImage {
  id: string;
  project_id: string;
  prompt: string;
  negative_prompt: string | null;
  width: number;
  height: number;
  num_inference_steps: number;
  guidance_scale: number;
  seed: number | null;
  file_path: string | null;
  file_size_bytes: number | null;
  status: "pending" | "queued" | "generating" | "completed" | "failed";
  error_message: string | null;
  generation_time_seconds: number | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Audio
// ============================================================

export interface AudioClip {
  id: string;
  project_id: string;
  text: string | null;
  voice_id: string | null;
  output_format: "wav" | "mp3" | "ogg";
  file_path: string | null;
  file_size_bytes: number | null;
  duration_seconds: number | null;
  clip_type: "tts" | "stt";
  status: "pending" | "queued" | "generating" | "completed" | "failed";
  error_message: string | null;
  generation_time_seconds: number | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Generation Job
// ============================================================

export interface GenerationJob {
  id: string;
  user_id: string;
  project_id: string | null;
  job_type: "image" | "video" | "audio" | "pipeline";
  status: "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";
  progress_percent: number;
  celery_task_id: string | null;
  result_url: string | null;
  error_message: string | null;
  duration_seconds: number | null;
  created_at: string;
  updated_at: string;
}
