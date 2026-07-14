/**
 * Shared Type Definitions.
 *
 * WHY this package exists:
 *   In a monorepo or multi-service setup, types shared between the
 *   backend (FastAPI) and frontend (Next.js) live here to avoid drift.
 *
 *   For Version 1 (local-only, single user), this is a documentation
 *   anchor that ensures the frontend's TypeScript interfaces stay
 *   in sync with the backend's Pydantic schemas.
 *
 *   Future: If a mobile app or CLI tool is added, they import from here.
 *
 * Note: In V1, these types are duplicated in frontend/src/types/.
 *       A build script or codegen tool (e.g. openapi-typescript) can
 *       automate keeping them in sync.
 */

export type JobStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ProjectStatus = "draft" | "generating" | "completed" | "failed";

export type MediaStatus = "pending" | "queued" | "generating" | "completed" | "failed";

export type LLMProvider = "gemma" | "llama" | "none";
export type ImageProvider = "stable_diffusion" | "none";
export type TTSProvider = "piper" | "none";
export type STTProvider = "whisper" | "none";
export type VideoProvider = "ffmpeg" | "none";
