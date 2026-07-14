/**
 * VideoGeneratorForm Component — Placeholder.
 *
 * WHY this component exists:
 *   The primary user interaction point for video creation.
 *   A multi-step form that collects:
 *     Step 1: Prompt + negative prompt
 *     Step 2: Video settings (frames, resolution, transition, fps)
 *     Step 3: Voice settings (voice ID, speed)
 *     Step 4: Review + Generate
 *
 *   On submit, calls POST /api/v1/videos/generate and redirects
 *   to the Video detail page, which polls for generation status.
 *
 * Implementation: Phase 8.
 */

export function VideoGeneratorForm() {
  return (
    <div className="glass-card p-8 text-center">
      <p className="text-white/40">VideoGeneratorForm — Phase 8</p>
    </div>
  );
}
