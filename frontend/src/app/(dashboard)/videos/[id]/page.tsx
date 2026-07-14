/**
 * Video Detail Page — /videos/[id]
 *
 * Shows the video player, generation details, download button,
 * and the frame images used in assembly.
 *
 * Implementation: Phase 8.
 */

export default function VideoDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Video: {params.id}</h1>
      <p className="text-white/40 text-sm">Implementation: Phase 8 — Video detail</p>
    </div>
  );
}
