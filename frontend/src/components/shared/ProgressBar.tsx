/**
 * ProgressBar Component.
 *
 * WHY this component exists:
 *   Shows real-time generation progress for videos and images.
 *   Connects to the polling hook to display live percent complete.
 *
 * Used in:
 *   - VideoCard (while generating)
 *   - ImageCard (while generating)
 *   - Dashboard job queue view
 */

import { cn } from "@/lib/utils";

interface ProgressBarProps {
  percent: number;       // 0–100
  label?: string;
  className?: string;
}

export function ProgressBar({ percent, label, className }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, percent));

  return (
    <div className={cn("space-y-1", className)}>
      {label && (
        <div className="flex justify-between text-xs text-white/40">
          <span>{label}</span>
          <span>{clamped}%</span>
        </div>
      )}
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-purple-500 transition-all duration-500"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
