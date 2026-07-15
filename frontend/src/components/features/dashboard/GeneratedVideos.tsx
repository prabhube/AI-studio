/**
 * GeneratedVideos — a gallery of the user's most recent video generations.
 *
 * Each tile shows a thumbnail placeholder, generation status, duration, file
 * size, and relative time, linking to the video detail page. Responsive grid:
 * 1 column on mobile, up to 3 on large screens.
 */

import Link from "next/link";
import { Play, Video as VideoIcon } from "lucide-react";

import {
  DashboardSection,
  SectionEmpty,
} from "@/components/features/dashboard/DashboardSection";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { ProgressBar } from "@/components/shared/ProgressBar";
import { cn, formatDuration, formatFileSize, timeAgo, truncate } from "@/lib/utils";
import type { Video } from "@/types/models";

interface GeneratedVideosProps {
  videos?: Video[];
  loading?: boolean;
}

export function GeneratedVideos({ videos, loading }: GeneratedVideosProps) {
  return (
    <DashboardSection
      title="Generated Videos"
      icon={VideoIcon}
      action={{ label: "View all", href: "/dashboard/videos" }}
    >
      {loading ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="overflow-hidden rounded-lg border border-white/5">
              <div className="skeleton aspect-video w-full rounded-none" />
              <div className="space-y-2 p-3">
                <div className="skeleton h-3.5 w-3/4" />
                <div className="skeleton h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : !videos || videos.length === 0 ? (
        <SectionEmpty
          icon={VideoIcon}
          title="No videos generated yet"
          description="Generate your first video from a text prompt to see it here."
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {videos.slice(0, 6).map((video) => (
            <VideoTile key={video.id} video={video} />
          ))}
        </div>
      )}
    </DashboardSection>
  );
}

function VideoTile({ video }: { video: Video }) {
  const inProgress = video.status === "generating" || video.status === "queued";

  return (
    <Link
      href={`/dashboard/videos/${video.id}`}
      className="group overflow-hidden rounded-lg border border-white/6 bg-surface-50 transition-all hover:border-white/12 hover:bg-surface-100"
    >
      {/* Thumbnail placeholder */}
      <div className="relative aspect-video w-full overflow-hidden bg-gradient-to-br from-brand-900/40 via-surface-100 to-purple-900/30">
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm transition-transform group-hover:scale-110">
            <Play className="h-5 w-5 translate-x-0.5 text-white" />
          </span>
        </div>

        <div className="absolute left-2 top-2">
          <StatusBadge status={video.status} />
        </div>

        {video.duration_seconds != null && (
          <span className="absolute bottom-2 right-2 rounded bg-black/60 px-1.5 py-0.5 text-xs font-medium text-white backdrop-blur-sm">
            {formatDuration(video.duration_seconds)}
          </span>
        )}
      </div>

      <div className="p-3">
        <p className="truncate text-sm font-medium text-white">
          {truncate(video.prompt, 60)}
        </p>

        {inProgress ? (
          <ProgressBar percent={40} className="mt-2" />
        ) : (
          <p className="mt-1 flex items-center gap-2 text-xs text-white/40">
            <span>{timeAgo(video.created_at)}</span>
            {video.file_size_bytes != null && (
              <>
                <span className={cn("h-1 w-1 rounded-full bg-white/20")} />
                <span>{formatFileSize(video.file_size_bytes)}</span>
              </>
            )}
          </p>
        )}
      </div>
    </Link>
  );
}
