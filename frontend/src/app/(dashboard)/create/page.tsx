"use client";

import { useEffect, useReducer, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
  Film,
  FolderOpen,
  Image as ImageIcon,
  Loader2,
  Mic,
  Music,
  User,
  Video,
  Wand2,
} from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import {
  analyzePrompt,
  assembleVideo,
  createSession,
  generateCharacters,
  generateImages,
  generateMusic,
  generateScenes,
  generateStory,
  generateSubtitles,
  generateVoice,
  getVideoDownloadUrl,
  reviewImages,
  reviewScenes,
  reviewStory,
} from "@/lib/pipeline-api";
import { PipelineProgress } from "@/components/features/pipeline/PipelineProgress";
import {
  IssueList,
  ReviewBadge,
  StepCard,
} from "@/components/features/pipeline/StepCard";
import type {
  CharacterSheet,
  ImageGenResult,
  ImageReviewResult,
  MusicGenResult,
  PipelineSession,
  PipelineStep,
  PromptAnalysis,
  SceneDetail,
  SceneReview,
  Story,
  StoryReview,
  SubtitleGenResult,
  VideoAssemblyResult,
  VoiceGenResult,
} from "@/types/pipeline";
import { useUIStore } from "@/store/ui-store";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

interface State {
  currentStep: PipelineStep;
  completedSteps: Set<PipelineStep>;
  loadingStep: PipelineStep | null;
  error: string | null;
  // Step 1
  prompt: string;
  numScenes: number;
  analysis: PromptAnalysis | null;
  // Steps 2-3
  story: Story | null;
  storyReview: StoryReview | null;
  // Steps 4-5
  sceneDetails: SceneDetail[] | null;
  sceneReview: SceneReview | null;
  // Step 6
  characters: CharacterSheet[] | null;
  // Step 7
  session: PipelineSession | null;
  // Step 8
  imageResult: ImageGenResult | null;
  imageWidth: number;
  imageHeight: number;
  // Step 9
  imageReview: ImageReviewResult | null;
  // Step 11
  voiceResult: VoiceGenResult | null;
  // Step 12
  musicResult: MusicGenResult | null;
  musicMood: string;
  // Step 13
  subtitleResult: SubtitleGenResult | null;
  // Steps 10+14
  videoResult: VideoAssemblyResult | null;
}

type Action =
  | { type: "SET_PROMPT"; value: string }
  | { type: "SET_NUM_SCENES"; value: number }
  | { type: "SET_IMAGE_SIZE"; width: number; height: number }
  | { type: "SET_MUSIC_MOOD"; value: string }
  | { type: "SET_LOADING"; step: PipelineStep | null }
  | { type: "SET_ERROR"; error: string | null }
  | { type: "STEP_DONE"; step: PipelineStep; next: PipelineStep }
  | { type: "SET_ANALYSIS"; analysis: PromptAnalysis }
  | { type: "SET_STORY"; story: Story }
  | { type: "SET_STORY_REVIEW"; review: StoryReview }
  | { type: "SET_SCENE_DETAILS"; scenes: SceneDetail[] }
  | { type: "SET_SCENE_REVIEW"; review: SceneReview }
  | { type: "SET_CHARACTERS"; characters: CharacterSheet[] }
  | { type: "SET_SESSION"; session: PipelineSession }
  | { type: "SET_IMAGE_RESULT"; result: ImageGenResult }
  | { type: "SET_IMAGE_REVIEW"; review: ImageReviewResult }
  | { type: "SET_VOICE_RESULT"; result: VoiceGenResult }
  | { type: "SET_MUSIC_RESULT"; result: MusicGenResult }
  | { type: "SET_SUBTITLE_RESULT"; result: SubtitleGenResult }
  | { type: "SET_VIDEO_RESULT"; result: VideoAssemblyResult };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_PROMPT":        return { ...state, prompt: action.value };
    case "SET_NUM_SCENES":    return { ...state, numScenes: action.value };
    case "SET_IMAGE_SIZE":    return { ...state, imageWidth: action.width, imageHeight: action.height };
    case "SET_MUSIC_MOOD":    return { ...state, musicMood: action.value };
    case "SET_LOADING":       return { ...state, loadingStep: action.step, error: null };
    case "SET_ERROR":         return { ...state, loadingStep: null, error: action.error };
    case "STEP_DONE": {
      const completed = new Set(state.completedSteps);
      completed.add(action.step);
      return { ...state, completedSteps: completed, currentStep: action.next, loadingStep: null, error: null };
    }
    case "SET_ANALYSIS":       return { ...state, analysis: action.analysis };
    case "SET_STORY":          return { ...state, story: action.story };
    case "SET_STORY_REVIEW":   return { ...state, storyReview: action.review };
    case "SET_SCENE_DETAILS":  return { ...state, sceneDetails: action.scenes };
    case "SET_SCENE_REVIEW":   return { ...state, sceneReview: action.review };
    case "SET_CHARACTERS":     return { ...state, characters: action.characters };
    case "SET_SESSION":        return { ...state, session: action.session };
    case "SET_IMAGE_RESULT":   return { ...state, imageResult: action.result };
    case "SET_IMAGE_REVIEW":   return { ...state, imageReview: action.review };
    case "SET_VOICE_RESULT":   return { ...state, voiceResult: action.result };
    case "SET_MUSIC_RESULT":   return { ...state, musicResult: action.result };
    case "SET_SUBTITLE_RESULT":return { ...state, subtitleResult: action.result };
    case "SET_VIDEO_RESULT":   return { ...state, videoResult: action.result };
    default:                   return state;
  }
}

const INITIAL_STATE: State = {
  currentStep: "prompt",
  completedSteps: new Set(),
  loadingStep: null,
  error: null,
  prompt: "",
  numScenes: 5,
  analysis: null,
  story: null,
  storyReview: null,
  sceneDetails: null,
  sceneReview: null,
  characters: null,
  session: null,
  imageResult: null,
  imageWidth: 512,
  imageHeight: 512,
  imageReview: null,
  voiceResult: null,
  musicResult: null,
  musicMood: "neutral",
  subtitleResult: null,
  videoResult: null,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function errMsg(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message;
  return fallback;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CreatePage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setPageTitle("Create Video");
    setPageBreadcrumbs([{ label: "Create Video" }]);
  }, [setPageTitle, setPageBreadcrumbs]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [state.currentStep]);

  // -------------------------------------------------------------------------
  // Step handlers
  // -------------------------------------------------------------------------

  async function handleAnalyze() {
    if (state.prompt.trim().length < 3) { toast.error("Enter at least 3 characters."); return; }
    dispatch({ type: "SET_LOADING", step: "prompt" });
    try {
      const analysis = await analyzePrompt(state.prompt.trim());
      dispatch({ type: "SET_ANALYSIS", analysis });
      dispatch({ type: "STEP_DONE", step: "prompt", next: "story" });
      toast.success("Prompt analyzed!");
    } catch (err) {
      const msg = errMsg(err, "Prompt analysis failed.");
      dispatch({ type: "SET_ERROR", error: msg });
      toast.error(msg);
    }
  }

  async function handleGenerateStory() {
    if (!state.analysis) return;
    dispatch({ type: "SET_LOADING", step: "story" });
    try {
      const story = await generateStory(state.analysis, state.numScenes);
      dispatch({ type: "SET_STORY", story });
      dispatch({ type: "STEP_DONE", step: "story", next: "story-review" });
      toast.success("Story generated!");
    } catch (err) {
      const msg = errMsg(err, "Story generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleReviewStory() {
    if (!state.story) return;
    dispatch({ type: "SET_LOADING", step: "story-review" });
    try {
      const review = await reviewStory(state.story, state.prompt);
      dispatch({ type: "SET_STORY_REVIEW", review });
      const next = review.revised_story ? "story-review" : "scenes";
      if (review.revised_story) dispatch({ type: "SET_STORY", story: review.revised_story });
      dispatch({ type: "STEP_DONE", step: "story-review", next: "scenes" });
      toast.success(review.approved ? "Story approved!" : "Story revised.");
    } catch (err) {
      const msg = errMsg(err, "Story review failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleGenerateScenes() {
    if (!state.story) return;
    dispatch({ type: "SET_LOADING", step: "scenes" });
    try {
      const scenes = await generateScenes(state.story, state.analysis?.style ?? "realistic");
      dispatch({ type: "SET_SCENE_DETAILS", scenes });
      dispatch({ type: "STEP_DONE", step: "scenes", next: "scene-review" });
      toast.success(`${scenes.length} scenes expanded!`);
    } catch (err) {
      const msg = errMsg(err, "Scene generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleReviewScenes() {
    if (!state.sceneDetails || !state.story) return;
    dispatch({ type: "SET_LOADING", step: "scene-review" });
    try {
      const review = await reviewScenes(state.sceneDetails, state.story.title);
      dispatch({ type: "SET_SCENE_REVIEW", review });
      if (review.revised_scenes) dispatch({ type: "SET_SCENE_DETAILS", scenes: review.revised_scenes });
      dispatch({ type: "STEP_DONE", step: "scene-review", next: "characters" });
      toast.success(review.approved ? "Scenes approved!" : "Scenes revised.");
    } catch (err) {
      const msg = errMsg(err, "Scene review failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleGenerateCharacters() {
    if (!state.analysis) return;
    dispatch({ type: "SET_LOADING", step: "characters" });
    try {
      const characters = await generateCharacters(state.analysis);
      dispatch({ type: "SET_CHARACTERS", characters });
      dispatch({ type: "STEP_DONE", step: "characters", next: "assets" });
      toast.success(`${characters.length} characters generated!`);
    } catch (err) {
      const msg = errMsg(err, "Character generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleCreateSession() {
    dispatch({ type: "SET_LOADING", step: "assets" });
    try {
      const session = await createSession();
      dispatch({ type: "SET_SESSION", session });
      dispatch({ type: "STEP_DONE", step: "assets", next: "images" });
      toast.success("Pipeline session created!");
    } catch (err) {
      const msg = errMsg(err, "Session creation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleGenerateImages() {
    if (!state.session || !state.sceneDetails) return;
    dispatch({ type: "SET_LOADING", step: "images" });
    try {
      const result = await generateImages(
        state.session.session_id, state.sceneDetails,
        state.imageWidth, state.imageHeight
      );
      dispatch({ type: "SET_IMAGE_RESULT", result });
      dispatch({ type: "STEP_DONE", step: "images", next: "image-review" });
      toast.success(`${result.count} images generated!`);
    } catch (err) {
      const msg = errMsg(err, "Image generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleReviewImages() {
    if (!state.session || !state.sceneDetails || !state.imageResult) return;
    dispatch({ type: "SET_LOADING", step: "image-review" });
    try {
      const review = await reviewImages(
        state.session.session_id, state.sceneDetails,
        state.imageResult.image_paths, state.analysis?.style ?? "realistic"
      );
      dispatch({ type: "SET_IMAGE_REVIEW", review });
      dispatch({ type: "STEP_DONE", step: "image-review", next: "voice" });
      toast.success(review.approved ? "Images approved!" : "Images need revision.");
    } catch (err) {
      const msg = errMsg(err, "Image review failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleGenerateVoice() {
    if (!state.session || !state.sceneDetails) return;
    dispatch({ type: "SET_LOADING", step: "voice" });
    try {
      const result = await generateVoice(
        state.session.session_id, state.sceneDetails,
        "en_US-lessac-medium", state.analysis?.language ?? "en"
      );
      dispatch({ type: "SET_VOICE_RESULT", result });
      dispatch({ type: "STEP_DONE", step: "voice", next: "music" });
      toast.success("Narration audio generated!");
    } catch (err) {
      const msg = errMsg(err, "Voice generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleGenerateMusic() {
    if (!state.session || !state.story) return;
    dispatch({ type: "SET_LOADING", step: "music" });
    try {
      const totalDuration = state.story.total_duration_seconds ?? 60;
      const result = await generateMusic(
        state.session.session_id, totalDuration, state.musicMood
      );
      dispatch({ type: "SET_MUSIC_RESULT", result });
      dispatch({ type: "STEP_DONE", step: "music", next: "subtitles" });
      toast.success("Background music generated!");
    } catch (err) {
      const msg = errMsg(err, "Music generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleGenerateSubtitles() {
    if (!state.session || !state.sceneDetails) return;
    dispatch({ type: "SET_LOADING", step: "subtitles" });
    try {
      const result = await generateSubtitles(state.session.session_id, state.sceneDetails);
      dispatch({ type: "SET_SUBTITLE_RESULT", result });
      dispatch({ type: "STEP_DONE", step: "subtitles", next: "editor" });
      toast.success("Subtitles generated!");
    } catch (err) {
      const msg = errMsg(err, "Subtitle generation failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  async function handleAssembleVideo() {
    if (!state.session || !state.sceneDetails || !state.imageResult) return;
    dispatch({ type: "SET_LOADING", step: "editor" });
    try {
      const result = await assembleVideo(
        state.session.session_id,
        state.sceneDetails,
        state.imageResult.image_paths,
        state.voiceResult?.narration_path ?? "",
        state.musicResult?.music_path ?? "",
        state.subtitleResult?.subtitle_path ?? "",
      );
      dispatch({ type: "SET_VIDEO_RESULT", result });
      dispatch({ type: "STEP_DONE", step: "editor", next: "export" });
      if (result.success) toast.success("Video assembled!");
      else toast.warning(result.error || "Assembly finished with warnings.");
    } catch (err) {
      const msg = errMsg(err, "Video assembly failed.");
      dispatch({ type: "SET_ERROR", error: msg }); toast.error(msg);
    }
  }

  // -------------------------------------------------------------------------
  // Render helpers
  // -------------------------------------------------------------------------

  const isLoading = (step: PipelineStep) => state.loadingStep === step;
  const isDone    = (step: PipelineStep) => state.completedSteps.has(step);
  const isActive  = (step: PipelineStep) => state.currentStep === step;

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-brand-600/[0.15] flex items-center justify-center">
          <Wand2 className="h-5 w-5 text-brand-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Create Video</h1>
          <p className="text-sm text-white/50">15-step AI pipeline · prompt → final video</p>
        </div>
      </div>

      {/* Progress bar */}
      <PipelineProgress
        completedSteps={state.completedSteps}
        currentStep={state.currentStep}
        loadingStep={state.loadingStep}
      />

      {/* Steps */}
      <div className="space-y-4" ref={bottomRef}>

        {/* ── STEP 1: Prompt Analyzer ─────────────────────────────────────── */}
        <StepSection
          step={1}
          title="Prompt Analyzer"
          icon={<Wand2 className="h-4 w-4" />}
          active={isActive("prompt")}
          done={isDone("prompt")}
        >
          <div className="space-y-4">
            <textarea
              value={state.prompt}
              onChange={(e) => dispatch({ type: "SET_PROMPT", value: e.target.value })}
              disabled={isDone("prompt")}
              placeholder="Describe your video idea… e.g. 'A short motivational video about achieving dreams, cinematic style, 5 scenes'"
              className="w-full min-h-[100px] rounded-xl bg-white/[0.05] border border-white/[0.1] px-4 py-3 text-white placeholder:text-white/30 text-sm resize-none focus:outline-none focus:border-brand-500"
            />
            <div className="flex items-center gap-4">
              <label className="text-sm text-white/60">
                Scenes:
                <select
                  value={state.numScenes}
                  onChange={(e) => dispatch({ type: "SET_NUM_SCENES", value: +e.target.value })}
                  disabled={isDone("prompt")}
                  className="ml-2 bg-white/[0.05] border border-white/[0.1] text-white rounded-lg px-2 py-1 text-sm"
                >
                  {[3, 4, 5, 6, 7, 8].map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              </label>
              <StepButton
                onClick={handleAnalyze}
                loading={isLoading("prompt")}
                done={isDone("prompt")}
                label="Analyze Prompt"
              />
            </div>
            {state.analysis && (
              <AnalysisCard analysis={state.analysis} />
            )}
          </div>
        </StepSection>

        {/* ── STEP 2: Story Generator ─────────────────────────────────────── */}
        {(isDone("prompt") || isActive("story")) && (
          <StepSection step={2} title="Story Generator" icon={<Film className="h-4 w-4" />}
            active={isActive("story")} done={isDone("story")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Generating a {state.numScenes}-scene story from your analyzed prompt.
              </p>
              <StepButton onClick={handleGenerateStory} loading={isLoading("story")}
                done={isDone("story")} label="Generate Story" />
              {state.story && <StoryCard story={state.story} />}
            </div>
          </StepSection>
        )}

        {/* ── STEP 3: Story Reviewer ──────────────────────────────────────── */}
        {(isDone("story") || isActive("story-review")) && (
          <StepSection step={3} title="Story Reviewer" icon={<CheckCircle2 className="h-4 w-4" />}
            active={isActive("story-review")} done={isDone("story-review")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                An AI reviewer checks the story for quality, coherence, and engagement.
              </p>
              <StepButton onClick={handleReviewStory} loading={isLoading("story-review")}
                done={isDone("story-review")} label="Review Story" />
              {state.storyReview && (
                <div className="space-y-2">
                  <ReviewBadge score={state.storyReview.quality_score} approved={state.storyReview.approved} />
                  <IssueList issues={state.storyReview.issues} suggestions={state.storyReview.suggestions} />
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 4: Scene Generator ─────────────────────────────────────── */}
        {(isDone("story-review") || isActive("scenes")) && (
          <StepSection step={4} title="Scene Generator" icon={<Film className="h-4 w-4" />}
            active={isActive("scenes")} done={isDone("scenes")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Each scene is expanded with image prompts, camera angles, and lighting directions.
              </p>
              <StepButton onClick={handleGenerateScenes} loading={isLoading("scenes")}
                done={isDone("scenes")} label="Generate Scenes" />
              {state.sceneDetails && <ScenesGrid scenes={state.sceneDetails} />}
            </div>
          </StepSection>
        )}

        {/* ── STEP 5: Scene Reviewer ──────────────────────────────────────── */}
        {(isDone("scenes") || isActive("scene-review")) && (
          <StepSection step={5} title="Scene Reviewer" icon={<CheckCircle2 className="h-4 w-4" />}
            active={isActive("scene-review")} done={isDone("scene-review")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Reviews scene image prompts for Stable Diffusion readiness.
              </p>
              <StepButton onClick={handleReviewScenes} loading={isLoading("scene-review")}
                done={isDone("scene-review")} label="Review Scenes" />
              {state.sceneReview && (
                <div className="space-y-2">
                  <ReviewBadge score={state.sceneReview.quality_score} approved={state.sceneReview.approved} />
                  <IssueList issues={state.sceneReview.issues} suggestions={state.sceneReview.suggestions} />
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 6: Character Generator ─────────────────────────────────── */}
        {(isDone("scene-review") || isActive("characters")) && (
          <StepSection step={6} title="Character Generator" icon={<User className="h-4 w-4" />}
            active={isActive("characters")} done={isDone("characters")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Generates detailed character sheets with appearance, personality, and voice descriptions.
              </p>
              <StepButton onClick={handleGenerateCharacters} loading={isLoading("characters")}
                done={isDone("characters")} label="Generate Characters" />
              {state.characters && state.characters.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {state.characters.map((ch, i) => (
                    <CharacterCard key={i} character={ch} />
                  ))}
                </div>
              )}
              {state.characters?.length === 0 && (
                <p className="text-sm text-white/40 italic">No named characters in this story.</p>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 7: Asset Manager ───────────────────────────────────────── */}
        {(isDone("characters") || isActive("assets")) && (
          <StepSection step={7} title="Asset Manager" icon={<FolderOpen className="h-4 w-4" />}
            active={isActive("assets")} done={isDone("assets")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Creates a pipeline session with dedicated directories for all generated assets.
              </p>
              <StepButton onClick={handleCreateSession} loading={isLoading("assets")}
                done={isDone("assets")} label="Create Session" />
              {state.session && (
                <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 space-y-2">
                  <p className="text-xs font-mono text-brand-400">
                    Session: {state.session.session_id}
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs text-white/50">
                    <span>📁 images/</span>
                    <span>🎵 audio/</span>
                    <span>📝 subtitles/</span>
                    <span>🎬 video/</span>
                  </div>
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 8: Image Generator ─────────────────────────────────────── */}
        {(isDone("assets") || isActive("images")) && (
          <StepSection step={8} title="Image Generator" icon={<ImageIcon className="h-4 w-4" />}
            active={isActive("images")} done={isDone("images")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Generates one image per scene using Stable Diffusion WebUI (if available) or
                high-quality placeholder images.
              </p>
              <div className="flex items-center gap-3 flex-wrap">
                <label className="text-sm text-white/60">
                  Size:
                  <select
                    value={`${state.imageWidth}x${state.imageHeight}`}
                    onChange={(e) => {
                      const parts = e.target.value.split("x");
                      const w = parseInt(parts[0] ?? "512", 10);
                      const h = parseInt(parts[1] ?? "512", 10);
                      dispatch({ type: "SET_IMAGE_SIZE", width: w, height: h });
                    }}
                    disabled={isDone("images")}
                    className="ml-2 bg-white/[0.05] border border-white/[0.1] text-white rounded-lg px-2 py-1 text-sm"
                  >
                    <option value="512x512">512×512</option>
                    <option value="768x512">768×512 (landscape)</option>
                    <option value="512x768">512×768 (portrait)</option>
                    <option value="768x768">768×768</option>
                  </select>
                </label>
                <StepButton onClick={handleGenerateImages} loading={isLoading("images")}
                  done={isDone("images")} label="Generate Images" />
              </div>
              {state.imageResult && state.session && (
                <ImageGrid sessionId={state.session.session_id} result={state.imageResult} />
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 9: Image Reviewer ──────────────────────────────────────── */}
        {(isDone("images") || isActive("image-review")) && (
          <StepSection step={9} title="Image Reviewer" icon={<CheckCircle2 className="h-4 w-4" />}
            active={isActive("image-review")} done={isDone("image-review")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Reviews the generated images for quality, style consistency, and video readiness.
              </p>
              <StepButton onClick={handleReviewImages} loading={isLoading("image-review")}
                done={isDone("image-review")} label="Review Images" />
              {state.imageReview && (
                <div className="space-y-3">
                  <ReviewBadge score={state.imageReview.overall_score} approved={state.imageReview.approved} />
                  <p className="text-xs text-white/50">
                    Ready for video: {state.imageReview.ready_for_video ? "✅ Yes" : "⚠️ Needs work"}
                  </p>
                  <IssueList issues={state.imageReview.consistency_issues} suggestions={state.imageReview.suggestions} />
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 10 (Video Generator) is combined into Step 14 (Video Editor) */}

        {/* ── STEP 11: Voice Generator ─────────────────────────────────────── */}
        {(isDone("image-review") || isActive("voice")) && (
          <StepSection step={11} title="Voice Generator" icon={<Mic className="h-4 w-4" />}
            active={isActive("voice")} done={isDone("voice")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Synthesizes narration audio using Piper TTS (offline), gTTS (online), or
                generates silence as a fallback.
              </p>
              <StepButton onClick={handleGenerateVoice} loading={isLoading("voice")}
                done={isDone("voice")} label="Generate Narration" />
              {state.voiceResult && (
                <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 space-y-1">
                  <p className="text-xs text-white/60">Method: <span className="text-brand-400">{state.voiceResult.method}</span></p>
                  <p className="text-xs text-white/60">
                    Duration: ~{Math.round(state.voiceResult.total_duration_estimate)}s
                  </p>
                  <p className="text-xs text-white/40 break-all">{state.voiceResult.narration_path}</p>
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 12: Music Generator ─────────────────────────────────────── */}
        {(isDone("voice") || isActive("music")) && (
          <StepSection step={12} title="Music Generator" icon={<Music className="h-4 w-4" />}
            active={isActive("music")} done={isDone("music")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Generates ambient background music using FFmpeg audio synthesis — no external files needed.
              </p>
              <div className="flex items-center gap-3">
                <label className="text-sm text-white/60">
                  Mood:
                  <select
                    value={state.musicMood}
                    onChange={(e) => dispatch({ type: "SET_MUSIC_MOOD", value: e.target.value })}
                    disabled={isDone("music")}
                    className="ml-2 bg-white/[0.05] border border-white/[0.1] text-white rounded-lg px-2 py-1 text-sm"
                  >
                    {["calm","neutral","cheerful","energetic","dramatic","suspenseful","inspirational","somber"].map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </label>
                <StepButton onClick={handleGenerateMusic} loading={isLoading("music")}
                  done={isDone("music")} label="Generate Music" />
              </div>
              {state.musicResult && (
                <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4">
                  <p className="text-xs text-white/60">Mood: <span className="text-brand-400">{state.musicResult.mood}</span></p>
                  <p className="text-xs text-white/40 mt-1 break-all">{state.musicResult.music_path}</p>
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 13: Subtitle Generator ──────────────────────────────────── */}
        {(isDone("music") || isActive("subtitles")) && (
          <StepSection step={13} title="Subtitle Generator" icon={<Film className="h-4 w-4" />}
            active={isActive("subtitles")} done={isDone("subtitles")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Generates SRT subtitles from scene narration text and timing data — no Whisper needed.
              </p>
              <StepButton onClick={handleGenerateSubtitles} loading={isLoading("subtitles")}
                done={isDone("subtitles")} label="Generate Subtitles" />
              {state.subtitleResult && (
                <div className="space-y-2">
                  <div className="rounded-xl bg-black/30 border border-white/[0.08] p-4">
                    <p className="text-xs text-white/40 mb-2 font-mono">subtitles.srt preview</p>
                    <pre className="text-xs text-white/70 font-mono whitespace-pre-wrap max-h-32 overflow-auto">
                      {state.subtitleResult.srt_preview}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEPS 10+14: Video Editor ────────────────────────────────────── */}
        {(isDone("subtitles") || isActive("editor")) && (
          <StepSection step={14} title="Video Editor" icon={<Video className="h-4 w-4" />}
            active={isActive("editor")} done={isDone("editor")}>
            <div className="space-y-4">
              <p className="text-sm text-white/60">
                Assembles the final video: images → silent video → add narration, music, subtitles.
                Requires <span className="text-brand-400">FFmpeg</span> installed in PATH.
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs text-white/50">
                <AssetStatus label="Images" ok={!!state.imageResult} count={state.imageResult?.count} />
                <AssetStatus label="Narration" ok={!!state.voiceResult} note={state.voiceResult?.method} />
                <AssetStatus label="Music" ok={!!state.musicResult} note={state.musicResult?.mood} />
                <AssetStatus label="Subtitles" ok={!!state.subtitleResult} />
              </div>
              <StepButton onClick={handleAssembleVideo} loading={isLoading("editor")}
                done={isDone("editor")} label="Assemble Video" />
              {state.videoResult && (
                <VideoResultCard result={state.videoResult} />
              )}
            </div>
          </StepSection>
        )}

        {/* ── STEP 15: Export ──────────────────────────────────────────────── */}
        {(isDone("editor") || isActive("export")) && (
          <StepSection step={15} title="Export" icon={<Download className="h-4 w-4" />}
            active={isActive("export")} done={isDone("export")} highlight>
            <div className="space-y-4">
              {state.videoResult?.success ? (
                <>
                  <p className="text-sm text-white/80">
                    Your video is ready! Click below to download the final MP4.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    {state.session && (
                      <a
                        href={getVideoDownloadUrl(state.session.session_id)}
                        download
                        className="inline-flex items-center gap-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium px-5 py-2.5 transition-colors"
                      >
                        <Download className="h-4 w-4" />
                        Download Video (MP4)
                      </a>
                    )}
                    <button
                      onClick={() => {
                        dispatch({ type: "STEP_DONE", step: "export", next: "export" });
                        toast.success("Export complete!");
                      }}
                      className="inline-flex items-center gap-2 rounded-xl bg-white/[0.08] hover:bg-white/[0.12] text-white text-sm px-5 py-2.5 transition-colors"
                    >
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      Mark Complete
                    </button>
                  </div>
                  <VideoDetails result={state.videoResult} />
                </>
              ) : (
                <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 p-4">
                  <p className="text-sm text-amber-300">
                    ⚠️ {state.videoResult?.error || "Video assembly did not produce a downloadable file. FFmpeg may not be installed."}
                  </p>
                  <p className="text-xs text-white/50 mt-2">
                    Install FFmpeg and re-run the Video Editor step to generate a downloadable video.
                  </p>
                </div>
              )}
            </div>
          </StepSection>
        )}
      </div>

      {/* Error banner */}
      {state.error && (
        <div className="flex items-start gap-3 rounded-xl bg-red-500/10 border border-red-500/30 p-4">
          <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm text-red-300 font-medium">Error</p>
            <p className="text-xs text-red-300/70 mt-0.5">{state.error}</p>
          </div>
          <button onClick={() => dispatch({ type: "SET_ERROR", error: null })}
            className="ml-auto text-red-400/60 hover:text-red-400 text-xs">Dismiss</button>
        </div>
      )}
    </div>
  );
}

// ===========================================================================
// Sub-components
// ===========================================================================

function StepSection({
  step, title, icon, active, done, highlight = false, children,
}: {
  step: number; title: string; icon: React.ReactNode;
  active: boolean; done: boolean; highlight?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(active || done);
  useEffect(() => { if (active) setOpen(true); }, [active]);

  return (
    <div className={cn(
      "rounded-2xl border transition-all",
      active && "border-brand-500/40 bg-brand-600/[0.06] shadow-lg shadow-brand-500/10",
      !active && done && "border-green-500/20 bg-green-500/[0.03]",
      !active && !done && "border-white/[0.06] bg-white/[0.02]",
      highlight && active && "border-brand-500/60 shadow-xl shadow-brand-500/20",
    )}>
      {/* Header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-3 p-4 text-left"
      >
        <span className={cn(
          "flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold shrink-0",
          done ? "bg-green-500 text-white" : active ? "bg-brand-500 text-white" : "bg-white/[0.08] text-white/40",
        )}>
          {done ? <CheckCircle2 className="h-4 w-4" /> : step}
        </span>
        <span className={cn("flex items-center gap-2 font-medium text-sm",
          active ? "text-white" : done ? "text-green-300" : "text-white/50")}>
          {icon} {title}
        </span>
        <span className="ml-auto text-white/30">
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </span>
      </button>

      {/* Body */}
      {open && (
        <div className="px-4 pb-4 border-t border-white/[0.04] pt-4">
          {children}
        </div>
      )}
    </div>
  );
}

function StepButton({
  onClick, loading, done, label,
}: {
  onClick: () => void; loading: boolean; done: boolean; label: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading || done}
      className={cn(
        "inline-flex items-center gap-2 rounded-xl text-sm font-medium px-4 py-2 transition-all",
        done
          ? "bg-green-500/20 text-green-300 cursor-default"
          : loading
          ? "bg-brand-600/50 text-white/60 cursor-wait"
          : "bg-brand-600 hover:bg-brand-500 text-white shadow-md shadow-brand-500/20",
      )}
    >
      {loading ? (
        <><Loader2 className="h-4 w-4 animate-spin" /> Running…</>
      ) : done ? (
        <><CheckCircle2 className="h-4 w-4" /> Done</>
      ) : (
        <><ArrowRight className="h-4 w-4" /> {label}</>
      )}
    </button>
  );
}

// ── Step 1: Analysis card ────────────────────────────────────────────────────

function AnalysisCard({ analysis }: { analysis: PromptAnalysis }) {
  return (
    <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
      {[
        ["Topic", analysis.topic],
        ["Mood", analysis.mood],
        ["Style", analysis.style],
        ["Audience", analysis.audience],
        ["Duration", `${analysis.duration_seconds}s`],
        ["Language", analysis.language],
        ["Camera", analysis.camera],
        ["Voice", analysis.voice],
      ].map(([k, v]) => (
        <div key={k}>
          <span className="text-white/40">{k}</span>
          <p className="text-white/80 mt-0.5 font-medium">{v}</p>
        </div>
      ))}
      {analysis.characters.length > 0 && (
        <div className="col-span-full">
          <span className="text-white/40">Characters</span>
          <p className="text-white/80 mt-0.5">
            {analysis.characters.map((c) => c.name).join(", ")}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Step 2: Story card ───────────────────────────────────────────────────────

function StoryCard({ story }: { story: Story }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 space-y-3">
      <div>
        <h3 className="text-white font-semibold">{story.title}</h3>
        <p className="text-xs text-white/50 mt-1">{story.synopsis}</p>
      </div>
      <div className="flex gap-3 text-xs text-white/40">
        <span>{story.genre}</span>
        <span>·</span>
        <span>{story.total_duration_seconds}s total</span>
        <span>·</span>
        <span>{story.scenes.length} scenes</span>
      </div>
      <button onClick={() => setExpanded((e) => !e)} className="text-xs text-brand-400 hover:text-brand-300">
        {expanded ? "Hide scenes ▲" : "Show scenes ▼"}
      </button>
      {expanded && (
        <div className="space-y-2">
          {story.scenes.map((scene) => (
            <div key={scene.index} className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3">
              <p className="text-xs font-medium text-white/80">#{scene.index + 1} {scene.title}</p>
              <p className="text-xs text-white/40 mt-1">{scene.narration}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Step 4: Scenes grid ──────────────────────────────────────────────────────

function ScenesGrid({ scenes }: { scenes: SceneDetail[] }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? scenes : scenes.slice(0, 2);
  return (
    <div className="space-y-2">
      {visible.map((scene) => (
        <div key={scene.index} className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-3 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-brand-400">#{scene.index + 1}</span>
            <span className="text-xs font-medium text-white/80">{scene.title}</span>
            <span className="ml-auto text-xs text-white/30">{scene.duration_seconds}s</span>
          </div>
          <p className="text-xs text-white/50">{scene.image_prompt.slice(0, 120)}…</p>
          <div className="flex gap-2 text-xs text-white/30">
            <span>📷 {scene.camera_angle}</span>
            <span>💡 {scene.lighting}</span>
          </div>
        </div>
      ))}
      {scenes.length > 2 && (
        <button onClick={() => setExpanded((e) => !e)} className="text-xs text-brand-400 hover:text-brand-300">
          {expanded ? `Show less ▲` : `Show ${scenes.length - 2} more scenes ▼`}
        </button>
      )}
    </div>
  );
}

// ── Step 6: Character card ───────────────────────────────────────────────────

function CharacterCard({ character }: { character: CharacterSheet }) {
  return (
    <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 space-y-2">
      <div className="flex items-center gap-2">
        <div className="h-7 w-7 rounded-full bg-brand-600/[0.3] flex items-center justify-center">
          <User className="h-3 w-3 text-brand-400" />
        </div>
        <div>
          <p className="text-xs font-semibold text-white">{character.name}</p>
          <p className="text-xs text-white/40">{character.role}</p>
        </div>
      </div>
      <p className="text-xs text-white/60">{character.appearance.slice(0, 120)}</p>
      <p className="text-xs text-white/40 italic">Voice: {character.voice_description}</p>
    </div>
  );
}

// ── Step 8: Image grid ───────────────────────────────────────────────────────

function ImageGrid({ sessionId, result }: { sessionId: string; result: ImageGenResult }) {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  return (
    <div className="space-y-2">
      <p className="text-xs text-white/40">
        {result.count} images · {result.sd_used ? "Stable Diffusion" : "Placeholder (SD not detected)"}
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {result.image_urls.map((url, i) => {
          const filename = url.split("/").pop();
          const fullUrl = `${base}/pipeline/images/${sessionId}/${filename}`;
          return (
            <div key={i} className="aspect-square rounded-lg overflow-hidden border border-white/[0.08] bg-white/[0.04]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={fullUrl}
                alt={`Scene ${i + 1}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Steps 10+14: Video result ────────────────────────────────────────────────

function VideoResultCard({ result }: { result: VideoAssemblyResult }) {
  return (
    <div className={cn(
      "rounded-xl border p-4 space-y-2",
      result.success ? "bg-green-500/[0.06] border-green-500/20" : "bg-amber-500/10 border-amber-500/30",
    )}>
      <div className="flex items-center gap-2">
        {result.success
          ? <CheckCircle2 className="h-4 w-4 text-green-400" />
          : <AlertCircle className="h-4 w-4 text-amber-400" />}
        <span className="text-sm font-medium text-white">
          {result.success ? "Assembly successful!" : "Assembly warning"}
        </span>
        <span className="ml-auto text-xs text-white/40">{result.method}</span>
      </div>
      {result.error && <p className="text-xs text-amber-300">{result.error}</p>}
      {result.final_path && (
        <p className="text-xs text-white/40 font-mono break-all">{result.final_path}</p>
      )}
    </div>
  );
}

// ── Step 15: Video details ───────────────────────────────────────────────────

function VideoDetails({ result }: { result: VideoAssemblyResult }) {
  return (
    <div className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 space-y-1 text-xs">
      <p className="text-white/40">Method: <span className="text-white/70">{result.method}</span></p>
      {result.final_path && (
        <p className="text-white/40 break-all">File: <span className="text-white/70 font-mono">{result.final_path}</span></p>
      )}
    </div>
  );
}

// ── Asset status indicator ───────────────────────────────────────────────────

function AssetStatus({ label, ok, count, note }: { label: string; ok: boolean; count?: number | null; note?: string }) {
  return (
    <div className={cn(
      "rounded-lg border px-3 py-2 flex items-center gap-2",
      ok ? "border-green-500/20 bg-green-500/[0.06]" : "border-white/[0.06] bg-white/[0.02]",
    )}>
      <span className={ok ? "text-green-400" : "text-white/20"}>
        {ok ? "✓" : "○"}
      </span>
      <span className={ok ? "text-white/70" : "text-white/30"}>
        {label}{count != null ? ` (${count})` : note ? ` · ${note}` : ""}
      </span>
    </div>
  );
}
