/**
 * ActivityTimeline — a chronological feed of recent account activity.
 *
 * Renders a vertical timeline of typed events (projects created, media
 * generated, credits spent, …), each with a type-specific icon and colour.
 * Rows link out when the event carries an `href`.
 */

import Link from "next/link";
import {
  Activity,
  Coins,
  FolderPlus,
  Image as ImageIcon,
  Mic,
  Video as VideoIcon,
  XCircle,
  type LucideIcon,
} from "lucide-react";

import {
  DashboardSection,
  SectionEmpty,
  SkeletonRow,
} from "@/components/features/dashboard/DashboardSection";
import { cn, timeAgo } from "@/lib/utils";
import type { ActivityEvent, ActivityType } from "@/types/dashboard";

const EVENT_STYLES: Record<ActivityType, { icon: LucideIcon; color: string; bg: string }> = {
  project_created:    { icon: FolderPlus, color: "text-brand-400",   bg: "bg-brand-600/15" },
  video_generated:    { icon: VideoIcon,  color: "text-sky-400",     bg: "bg-sky-500/15" },
  video_failed:       { icon: XCircle,    color: "text-red-400",     bg: "bg-red-500/15" },
  image_generated:    { icon: ImageIcon,  color: "text-violet-400",  bg: "bg-violet-500/15" },
  audio_generated:    { icon: Mic,        color: "text-emerald-400", bg: "bg-emerald-500/15" },
  credits_purchased:  { icon: Coins,      color: "text-amber-400",   bg: "bg-amber-500/15" },
  credits_spent:      { icon: Coins,      color: "text-white/60",    bg: "bg-white/8" },
};

const FALLBACK_STYLE = { icon: Activity, color: "text-white/60", bg: "bg-white/8" };

interface ActivityTimelineProps {
  events?: ActivityEvent[];
  loading?: boolean;
}

export function ActivityTimeline({ events, loading }: ActivityTimelineProps) {
  return (
    <DashboardSection title="Activity Timeline" icon={Activity}>
      {loading ? (
        <ul className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <li key={i} className="flex items-center gap-3">
              <div className="skeleton h-8 w-8 flex-shrink-0 rounded-full" />
              <div className="flex-1 space-y-2">
                <SkeletonRow className="h-3.5 w-2/3" />
                <SkeletonRow className="h-3 w-1/3" />
              </div>
            </li>
          ))}
        </ul>
      ) : !events || events.length === 0 ? (
        <SectionEmpty
          icon={Activity}
          title="No activity yet"
          description="Your recent generations and account events will appear here."
        />
      ) : (
        <ol className="relative space-y-5">
          {/* Connecting line */}
          <span
            aria-hidden
            className="absolute bottom-2 left-4 top-2 w-px bg-white/8"
          />
          {events.slice(0, 8).map((event) => (
            <ActivityRow key={event.id} event={event} />
          ))}
        </ol>
      )}
    </DashboardSection>
  );
}

function ActivityRow({ event }: { event: ActivityEvent }) {
  const style = EVENT_STYLES[event.type] ?? FALLBACK_STYLE;
  const Icon = style.icon;

  const body = (
    <>
      <span
        className={cn(
          "relative z-10 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ring-4 ring-surface-50",
          style.bg,
        )}
      >
        <Icon className={cn("h-4 w-4", style.color)} />
      </span>
      <span className="min-w-0 flex-1 pt-0.5">
        <span className="block text-sm font-medium text-white">
          {event.title}
        </span>
        {event.description && (
          <span className="block truncate text-xs text-white/45">
            {event.description}
          </span>
        )}
        <span className="mt-0.5 block text-xs text-white/30">
          {timeAgo(event.created_at)}
        </span>
      </span>
    </>
  );

  return (
    <li className="relative flex gap-3">
      {event.href ? (
        <Link
          href={event.href}
          className="flex flex-1 gap-3 rounded-lg -m-1 p-1 transition-colors hover:bg-white/4"
        >
          {body}
        </Link>
      ) : (
        body
      )}
    </li>
  );
}
