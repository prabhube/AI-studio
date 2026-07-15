/**
 * Pipeline TypeScript types — mirrors backend app/schemas/story.py
 * and app/schemas/prompt.py.
 */

// ---------------------------------------------------------------------------
// Step 1: Prompt Analysis
// ---------------------------------------------------------------------------

export interface PromptCharacter {
  name: string;
  description?: string | null;
  role?: string | null;
}

export interface PromptAnalysis {
  topic: string;
  audience: string;
  mood: string;
  characters: PromptCharacter[];
  style: string;
  camera: string;
  duration_seconds: number;
  language: string;
  voice: string;
}

// ---------------------------------------------------------------------------
// Step 2 & 3: Story
// ---------------------------------------------------------------------------

export interface Scene {
  index: number;
  title: string;
  narration: string;
  image_prompt: string;
  duration_seconds: number;
  setting: string;
  mood: string;
}

export interface Story {
  title: string;
  synopsis: string;
  scenes: Scene[];
  total_duration_seconds: number;
  style_notes: string;
  target_audience: string;
  genre: string;
}

export interface StoryReview {
  quality_score: number;
  approved: boolean;
  issues: string[];
  suggestions: string[];
  revised_story: Story | null;
}

// ---------------------------------------------------------------------------
// Step 4 & 5: Scene Details
// ---------------------------------------------------------------------------

export interface SceneDetail {
  index: number;
  title: string;
  narration: string;
  image_prompt: string;
  negative_prompt: string;
  duration_seconds: number;
  setting: string;
  mood: string;
  camera_angle: string;
  lighting: string;
  characters_present: string[];
}

export interface SceneReview {
  quality_score: number;
  approved: boolean;
  issues: string[];
  suggestions: string[];
  revised_scenes: SceneDetail[] | null;
}

// ---------------------------------------------------------------------------
// Step 6: Characters
// ---------------------------------------------------------------------------

export interface CharacterSheet {
  name: string;
  role: string;
  appearance: string;
  image_prompt: string;
  personality: string;
  voice_description: string;
}

// ---------------------------------------------------------------------------
// Pipeline state (tracks the whole wizard)
// ---------------------------------------------------------------------------

export type PipelineStep =
  | "prompt"
  | "story"
  | "story-review"
  | "scenes"
  | "scene-review"
  | "characters"
  | "assets"
  | "images"
  | "image-review"
  | "video"
  | "voice"
  | "music"
  | "subtitles"
  | "editor"
  | "export";

export const PIPELINE_STEPS: { key: PipelineStep; label: string; step: number }[] = [
  { key: "prompt",       label: "Prompt Analyzer",    step: 1  },
  { key: "story",        label: "Story Generator",    step: 2  },
  { key: "story-review", label: "Story Reviewer",     step: 3  },
  { key: "scenes",       label: "Scene Generator",    step: 4  },
  { key: "scene-review", label: "Scene Reviewer",     step: 5  },
  { key: "characters",   label: "Character Generator",step: 6  },
  { key: "assets",       label: "Asset Manager",      step: 7  },
  { key: "images",       label: "Image Generator",    step: 8  },
  { key: "image-review", label: "Image Reviewer",     step: 9  },
  { key: "video",        label: "Video Generator",    step: 10 },
  { key: "voice",        label: "Voice Generator",    step: 11 },
  { key: "music",        label: "Music Generator",    step: 12 },
  { key: "subtitles",    label: "Subtitle Generator", step: 13 },
  { key: "editor",       label: "Video Editor",       step: 14 },
  { key: "export",       label: "Export",             step: 15 },
];

// ---------------------------------------------------------------------------
// Steps 7–15: Session & Asset types
// ---------------------------------------------------------------------------

export interface PipelineSession {
  session_id: string;
  root_dir: string;
  images_dir: string;
  audio_dir: string;
  subtitles_dir: string;
  video_dir: string;
  status: string;
}

export interface ImageGenResult {
  session_id: string;
  image_paths: string[];
  image_urls: string[];
  count: number;
  sd_used: boolean;
}

export interface ImageReviewResult {
  overall_score: number;
  approved: boolean;
  scene_scores: { index: number; score: number; issues: string[] }[];
  consistency_issues: string[];
  suggestions: string[];
  ready_for_video: boolean;
  image_count: number;
}

export interface VoiceGenResult {
  narration_path: string;
  method: string;
  total_duration_estimate: number;
}

export interface MusicGenResult {
  music_path: string;
  mood: string;
}

export interface SubtitleGenResult {
  subtitle_path: string;
  srt_preview: string;
}

export interface VideoAssemblyResult {
  final_path: string;
  assembled_path: string;
  method: string;
  success: boolean;
  error: string;
  download_url: string;
}

// ---------------------------------------------------------------------------
// Pipeline state (tracks the whole wizard — all 15 steps)
// ---------------------------------------------------------------------------

export interface PipelineState {
  currentStep: PipelineStep;
  prompt: string;
  analysis: PromptAnalysis | null;
  story: Story | null;
  storyReview: StoryReview | null;
  sceneDetails: SceneDetail[] | null;
  sceneReview: SceneReview | null;
  characters: CharacterSheet[] | null;
  // Steps 7-15
  session: PipelineSession | null;
  imageResult: ImageGenResult | null;
  imageReview: ImageReviewResult | null;
  voiceResult: VoiceGenResult | null;
  musicResult: MusicGenResult | null;
  subtitleResult: SubtitleGenResult | null;
  videoResult: VideoAssemblyResult | null;
}
