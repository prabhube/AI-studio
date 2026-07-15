/**
 * Pipeline API client — calls all 15 pipeline steps.
 * Mirrors backend/app/api/v1/endpoints/pipeline.py
 */

import apiClient from "@/lib/api-client";
import type {
  CharacterSheet,
  ImageGenResult,
  ImageReviewResult,
  MusicGenResult,
  PipelineSession,
  PromptAnalysis,
  SceneDetail,
  SceneReview,
  Story,
  StoryReview,
  SubtitleGenResult,
  VideoAssemblyResult,
  VoiceGenResult,
} from "@/types/pipeline";

interface ApiSuccess<T> {
  success: boolean;
  data: T;
  message?: string;
}

// ---------------------------------------------------------------------------
// Step 1 — Prompt Analysis
// ---------------------------------------------------------------------------

export const analyzePrompt = async (prompt: string): Promise<PromptAnalysis> => {
  const { data } = await apiClient.post<ApiSuccess<PromptAnalysis>>(
    "/pipeline/prompt/analyze",
    { prompt }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 2 — Story Generation
// ---------------------------------------------------------------------------

export const generateStory = async (
  analysis: PromptAnalysis,
  numScenes = 5
): Promise<Story> => {
  const { data } = await apiClient.post<ApiSuccess<Story>>(
    "/pipeline/story/generate",
    { analysis, num_scenes: numScenes }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 3 — Story Review
// ---------------------------------------------------------------------------

export const reviewStory = async (
  story: Story,
  originalPrompt: string
): Promise<StoryReview> => {
  const { data } = await apiClient.post<ApiSuccess<StoryReview>>(
    "/pipeline/story/review",
    { story, original_prompt: originalPrompt }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 4 — Scene Generation
// ---------------------------------------------------------------------------

export const generateScenes = async (
  story: Story,
  style = "realistic"
): Promise<SceneDetail[]> => {
  const { data } = await apiClient.post<ApiSuccess<SceneDetail[]>>(
    "/pipeline/scenes/generate",
    { story, style }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 5 — Scene Review
// ---------------------------------------------------------------------------

export const reviewScenes = async (
  scenes: SceneDetail[],
  storyTitle: string
): Promise<SceneReview> => {
  const { data } = await apiClient.post<ApiSuccess<SceneReview>>(
    "/pipeline/scenes/review",
    { scenes, story_title: storyTitle }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 6 — Character Generation
// ---------------------------------------------------------------------------

export const generateCharacters = async (
  analysis: PromptAnalysis
): Promise<CharacterSheet[]> => {
  const { data } = await apiClient.post<ApiSuccess<CharacterSheet[]>>(
    "/pipeline/characters/generate",
    { analysis }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 7 — Session / Asset Manager
// ---------------------------------------------------------------------------

export const createSession = async (): Promise<PipelineSession> => {
  const { data } = await apiClient.post<ApiSuccess<PipelineSession>>(
    "/pipeline/session"
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 8 — Image Generation
// ---------------------------------------------------------------------------

export const generateImages = async (
  sessionId: string,
  scenes: SceneDetail[],
  width = 512,
  height = 512,
  steps = 20
): Promise<ImageGenResult> => {
  const { data } = await apiClient.post<ApiSuccess<ImageGenResult>>(
    "/pipeline/images/generate",
    { session_id: sessionId, scenes, width, height, steps }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 9 — Image Review
// ---------------------------------------------------------------------------

export const reviewImages = async (
  sessionId: string,
  scenes: SceneDetail[],
  imagePaths: string[],
  style = "realistic"
): Promise<ImageReviewResult> => {
  const { data } = await apiClient.post<ApiSuccess<ImageReviewResult>>(
    "/pipeline/images/review",
    { session_id: sessionId, scenes, image_paths: imagePaths, style }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 11 — Voice Generation
// ---------------------------------------------------------------------------

export const generateVoice = async (
  sessionId: string,
  scenes: SceneDetail[],
  voiceId = "en_US-lessac-medium",
  language = "en",
  speed = 1.0
): Promise<VoiceGenResult> => {
  const { data } = await apiClient.post<ApiSuccess<VoiceGenResult>>(
    "/pipeline/voice/generate",
    { session_id: sessionId, scenes, voice_id: voiceId, language, speed }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 12 — Music Generation
// ---------------------------------------------------------------------------

export const generateMusic = async (
  sessionId: string,
  durationSeconds: number,
  mood = "neutral",
  volume = 0.15
): Promise<MusicGenResult> => {
  const { data } = await apiClient.post<ApiSuccess<MusicGenResult>>(
    "/pipeline/music/generate",
    { session_id: sessionId, duration_seconds: durationSeconds, mood, volume }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 13 — Subtitle Generation
// ---------------------------------------------------------------------------

export const generateSubtitles = async (
  sessionId: string,
  scenes: SceneDetail[]
): Promise<SubtitleGenResult> => {
  const { data } = await apiClient.post<ApiSuccess<SubtitleGenResult>>(
    "/pipeline/subtitles/generate",
    { session_id: sessionId, scenes }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Steps 10 + 14 — Video Assembly
// ---------------------------------------------------------------------------

export const assembleVideo = async (
  sessionId: string,
  scenes: SceneDetail[],
  imagePaths: string[],
  narrationPath = "",
  musicPath = "",
  subtitlePath = "",
  width = 1280,
  height = 720,
  fps = 24
): Promise<VideoAssemblyResult> => {
  const { data } = await apiClient.post<ApiSuccess<VideoAssemblyResult>>(
    "/pipeline/video/assemble",
    {
      session_id: sessionId,
      scenes,
      image_paths: imagePaths,
      narration_path: narrationPath,
      music_path: musicPath,
      subtitle_path: subtitlePath,
      width,
      height,
      fps,
    }
  );
  return data.data;
};

// ---------------------------------------------------------------------------
// Step 15 — Download URL builder
// ---------------------------------------------------------------------------

export const getVideoDownloadUrl = (sessionId: string): string => {
  const base =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  return `${base}/pipeline/video/${sessionId}/download`;
};

export const getImageUrl = (sessionId: string, filename: string): string => {
  const base =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  return `${base}/pipeline/images/${sessionId}/${filename}`;
};
