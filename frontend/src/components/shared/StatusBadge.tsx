/**
 * StatusBadge Component.
 *
 * WHY this component exists:
 *   Consistent, color-coded status indicators used across
 *   video cards, image cards, audio clip rows, and job tables.
 *
 * Status → Color mapping:
 *   pending     → gray
 *   queued      → yellow
 *   generating  → blue (pulsing)
 *   completed   → green
 *   failed      → red
 *   cancelled   → gray strikethrough
 *
 * Implementation: Phase 2 (used in project cards).
 */

import { cn } from "@/lib/utils";

type Status = "pending" | "queued" | "generating" | "completed" | "failed" | "cancelled";

const STATUS_STYLES: Record<Status, string> = {
  pending:    "bg-gray-500/20 text-gray-300 border-gray-500/30",
  queued:     "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  generating: "bg-blue-500/20 text-blue-300 border-blue-500/30 animate-pulse-slow",
  completed:  "bg-green-500/20 text-green-300 border-green-500/30",
  failed:     "bg-red-500/20 text-red-300 border-red-500/30",
  cancelled:  "bg-gray-500/10 text-gray-500 border-gray-500/20",
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const styles = STATUS_STYLES[status as Status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        styles,
        className,
      )}
    >
      {status}
    </span>
  );
}
