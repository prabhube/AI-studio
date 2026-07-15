"use client";

/**
 * Dashboard home page.
 *
 * Aggregated, glanceable overview of the studio:
 *  - Headline counters (projects / videos / images / audio)
 *  - Recent Projects
 *  - Generated Videos gallery
 *  - Credits balance
 *  - Storage usage (live disk data + per-type breakdown)
 *  - Activity timeline
 *  - Quick Generate entry point
 *  - Infrastructure health
 *
 * Data comes from a single aggregated read (useDashboardSummary → GET
 * /dashboard/summary). Every panel degrades gracefully to skeletons while
 * loading and to neutral empty states if data is unavailable, so the page is
 * production-safe even before every backend endpoint is live.
 */

import { useEffect } from "react";
import {
  Cpu,
  Database,
  FolderPlus,
  HardDrive,
  Image as ImageIcon,
  Mic,
  Video,
} from "lucide-react";

import { useUIStore } from "@/store/ui-store";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useSystemHealth, deriveOverallStatus } from "@/hooks/useSystemHealth";
import { StatCard } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { cn, formatNumber } from "@/lib/utils";

import { QuickGenerate } from "@/components/features/dashboard/QuickGenerate";
import { RecentProjects } from "@/components/features/dashboard/RecentProjects";
import { GeneratedVideos } from "@/components/features/dashboard/GeneratedVideos";
import { CreditsCard } from "@/components/features/dashboard/CreditsCard";
import { StorageUsageCard } from "@/components/features/dashboard/StorageUsageCard";
import { ActivityTimeline } from "@/components/features/dashboard/ActivityTimeline";
import type { DashboardStats } from "@/types/dashboard";

// ---------------------------------------------------------------------------
// Stats row
// ---------------------------------------------------------------------------

function toDelta(value?: number) {
  if (value == null || value === 0) return undefined;
  return { value: `${Math.abs(value)} this week`, positive: value > 0 };
}

function StatsRow({
  stats,
  loading,
}: {
  stats?: DashboardStats;
  loading?: boolean;
}) {
  const cards = [
    {
      label: "Projects",
      value: stats?.projects ?? 0,
      icon: <FolderPlus className="h-5 w-5" />,
      delta: toDelta(stats?.deltas?.projects),
    },
    {
      label: "Videos Generated",
      value: stats?.videos ?? 0,
      icon: <Video className="h-5 w-5" />,
      delta: toDelta(stats?.deltas?.videos),
    },
    {
      label: "Images Generated",
      value: stats?.images ?? 0,
      icon: <ImageIcon className="h-5 w-5" />,
      delta: toDelta(stats?.deltas?.images),
    },
    {
      label: "Audio Clips",
      value: stats?.audio_clips ?? 0,
      icon: <Mic className="h-5 w-5" />,
      delta: toDelta(stats?.deltas?.audio_clips),
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) =>
        loading ? (
          <div key={card.label} className="surface-card p-5">
            <div className="skeleton h-3 w-20" />
            <div className="skeleton mt-3 h-7 w-12" />
          </div>
        ) : (
          <StatCard
            key={card.label}
            label={card.label}
            value={formatNumber(Number(card.value))}
            icon={card.icon}
            delta={card.delta}
          />
        ),
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// System status panel
// ---------------------------------------------------------------------------

function SystemStatusPanel() {
  const { data, isLoading, isError } = useSystemHealth();
  const status = deriveOverallStatus(data, isError);

  const postgres = data?.services.postgres;
  const redis = data?.services.redis;

  const statusVariant = {
    healthy: "success",
    degraded: "warning",
    unhealthy: "danger",
    unknown: "default",
  } as const;

  return (
    <div className="surface-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Infrastructure</h2>
        {isLoading ? (
          <Spinner size="xs" variant="muted" />
        ) : (
          <Badge variant={statusVariant[status]}>
            {status === "healthy"
              ? "All Systems Operational"
              : status === "degraded"
                ? "Degraded"
                : status === "unhealthy"
                  ? "Service Issue"
                  : "Checking…"}
          </Badge>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {/* PostgreSQL */}
        <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/3 p-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-sky-500/10">
            <Database className="h-4 w-4 text-sky-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">PostgreSQL</p>
            <p className="text-xs text-white/40">
              {isLoading
                ? "…"
                : postgres?.status === "ok"
                  ? `${postgres.latency_ms?.toFixed(0) ?? "—"}ms`
                  : "Unavailable"}
            </p>
          </div>
          <span
            className={cn(
              "ml-auto h-2 w-2 flex-shrink-0 rounded-full",
              isLoading
                ? "animate-pulse bg-white/20"
                : postgres?.status === "ok"
                  ? "bg-emerald-400"
                  : "bg-red-400",
            )}
          />
        </div>

        {/* Redis */}
        <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/3 p-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-red-500/10">
            <Cpu className="h-4 w-4 text-red-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">Redis</p>
            <p className="text-xs text-white/40">
              {isLoading
                ? "…"
                : redis?.status === "ok"
                  ? `${redis.latency_ms?.toFixed(0) ?? "—"}ms`
                  : "Unavailable"}
            </p>
          </div>
          <span
            className={cn(
              "ml-auto h-2 w-2 flex-shrink-0 rounded-full",
              isLoading
                ? "animate-pulse bg-white/20"
                : redis?.status === "ok"
                  ? "bg-emerald-400"
                  : "bg-amber-400",
            )}
          />
        </div>

        {/* Disk */}
        <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/3 p-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-violet-500/10">
            <HardDrive className="h-4 w-4 text-violet-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">Disk</p>
            <p className="text-xs text-white/40">
              {isLoading
                ? "…"
                : data?.disk?.free_gb != null
                  ? `${data.disk.free_gb.toFixed(1)} GB free`
                  : "N/A"}
            </p>
          </div>
          <span
            className={cn(
              "ml-auto h-2 w-2 flex-shrink-0 rounded-full",
              isLoading
                ? "animate-pulse bg-white/20"
                : data?.disk?.percent_used != null && data.disk.percent_used > 90
                  ? "bg-red-400"
                  : "bg-emerald-400",
            )}
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();
  const { data, isLoading } = useDashboardSummary();

  useEffect(() => {
    setPageTitle("Dashboard");
    setPageBreadcrumbs([{ label: "Dashboard" }]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      {/* Page heading */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-white/40">
            Local-first AI video generation — all processing runs on your machine.
          </p>
        </div>
        <QuickGenerate className="self-start" />
      </div>

      {/* Stats row */}
      <StatsRow stats={data?.stats} loading={isLoading} />

      {/* Main grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Primary column */}
        <div className="space-y-6 lg:col-span-2">
          <GeneratedVideos videos={data?.recent_videos} loading={isLoading} />
          <RecentProjects projects={data?.recent_projects} loading={isLoading} />
        </div>

        {/* Side column */}
        <div className="space-y-6">
          <CreditsCard credits={data?.credits} loading={isLoading} />
          <StorageUsageCard storage={data?.storage} loading={isLoading} />
          <ActivityTimeline events={data?.activity} loading={isLoading} />
        </div>
      </div>

      {/* Infrastructure health */}
      <SystemStatusPanel />
    </div>
  );
}
