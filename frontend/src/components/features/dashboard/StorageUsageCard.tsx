/**
 * StorageUsageCard — media storage consumption.
 *
 * Data sources (in priority order):
 *   1. `storage` from the dashboard summary — per-user quota + per-type breakdown.
 *   2. Live disk info from the /health endpoint (useSystemHealth) — always
 *      available, used as a fallback so the card is meaningful even before the
 *      per-user storage aggregate exists.
 *
 * WHY the fallback? The backend already reports real disk free/used via health
 * checks, so we can render an accurate storage picture immediately and enrich it
 * with the type breakdown once the summary endpoint is live.
 */

"use client";

import { HardDrive } from "lucide-react";

import { useSystemHealth } from "@/hooks/useSystemHealth";
import { SkeletonRow } from "@/components/features/dashboard/DashboardSection";
import { clamp, formatFileSize } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { StorageUsage } from "@/types/dashboard";

const GB = 1024 ** 3;

const SEGMENTS = [
  { key: "videos", label: "Videos", color: "bg-brand-500" },
  { key: "images", label: "Images", color: "bg-sky-500" },
  { key: "audio", label: "Audio", color: "bg-emerald-500" },
  { key: "other", label: "Other", color: "bg-white/25" },
] as const;

interface StorageUsageCardProps {
  storage?: StorageUsage;
  loading?: boolean;
}

export function StorageUsageCard({ storage, loading }: StorageUsageCardProps) {
  const { data: health, isLoading: healthLoading } = useSystemHealth();

  // Prefer the per-user aggregate; fall back to live disk usage.
  let usedBytes = storage?.used_bytes ?? null;
  let totalBytes = storage?.total_bytes ?? null;

  if ((usedBytes === null || totalBytes === null) && health?.disk?.total_gb != null) {
    const total = health.disk.total_gb * GB;
    const free = (health.disk.free_gb ?? 0) * GB;
    totalBytes = total;
    usedBytes = Math.max(0, total - free);
  }

  const isLoading = loading || (usedBytes === null && healthLoading);
  const percent =
    usedBytes !== null && totalBytes
      ? clamp(Math.round((usedBytes / totalBytes) * 100), 0, 100)
      : 0;
  const critical = percent >= 90;

  return (
    <div className="surface-card flex flex-col p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <HardDrive className="h-4 w-4 text-violet-400" />
          <h2 className="text-sm font-semibold text-white">Storage Usage</h2>
        </div>
        {usedBytes !== null && !isLoading && (
          <span
            className={cn(
              "text-xs font-semibold",
              critical ? "text-red-300" : "text-white/50",
            )}
          >
            {percent}%
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <SkeletonRow className="h-6 w-40" />
          <SkeletonRow className="h-2.5" />
          <SkeletonRow className="h-4 w-3/4" />
        </div>
      ) : usedBytes === null || !totalBytes ? (
        <div className="flex flex-1 flex-col items-center justify-center py-6 text-center">
          <p className="text-sm font-medium text-white/80">Storage unavailable</p>
          <p className="mt-1 text-xs text-white/40">
            Disk usage could not be read right now.
          </p>
        </div>
      ) : (
        <div className="flex flex-1 flex-col">
          <p className="text-sm text-white/60">
            <span className="text-lg font-bold text-white">
              {formatFileSize(usedBytes)}
            </span>{" "}
            of {formatFileSize(totalBytes)} used
          </p>

          {/* Stacked usage bar */}
          <div className="mt-4 flex h-2.5 w-full overflow-hidden rounded-full bg-white/10">
            {storage ? (
              SEGMENTS.map((seg) => {
                const value = storage.by_type[seg.key] ?? 0;
                const segPercent = totalBytes ? (value / totalBytes) * 100 : 0;
                if (segPercent <= 0) return null;
                return (
                  <div
                    key={seg.key}
                    className={cn("h-full transition-all duration-500", seg.color)}
                    style={{ width: `${segPercent}%` }}
                  />
                );
              })
            ) : (
              <div
                className={cn(
                  "h-full rounded-full bg-gradient-to-r transition-all duration-500",
                  critical
                    ? "from-red-500 to-orange-500"
                    : "from-brand-500 to-purple-500",
                )}
                style={{ width: `${percent}%` }}
              />
            )}
          </div>

          {/* Legend — only when we have a per-type breakdown */}
          {storage && (
            <ul className="mt-4 grid grid-cols-2 gap-2">
              {SEGMENTS.map((seg) => (
                <li key={seg.key} className="flex items-center gap-2 text-xs">
                  <span className={cn("h-2 w-2 rounded-full", seg.color)} />
                  <span className="text-white/50">{seg.label}</span>
                  <span className="ml-auto font-medium text-white/70">
                    {formatFileSize(storage.by_type[seg.key] ?? 0)}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {critical && (
            <p className="mt-4 text-xs text-red-300">
              Storage is almost full — free up space to keep generating.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
