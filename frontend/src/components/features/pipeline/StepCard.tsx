"use client";

import { cn } from "@/lib/utils";

interface StepCardProps {
  step: number;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function StepCard({ step, title, description, children, className }: StepCardProps) {
  return (
    <div className={cn("surface-card p-6", className)}>
      <div className="mb-5 flex items-start gap-4">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-brand-600/[0.15] text-sm font-bold text-brand-400">
          {step}
        </div>
        <div>
          <h2 className="text-base font-semibold text-white">{title}</h2>
          {description && (
            <p className="mt-0.5 text-sm text-white/[0.45]">{description}</p>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

interface ReviewBadgeProps {
  score: number;
  approved: boolean;
}

export function ReviewBadge({ score, approved }: ReviewBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "rounded-full px-2.5 py-0.5 text-xs font-semibold",
          approved
            ? "bg-emerald-500/[0.15] text-emerald-400"
            : "bg-amber-500/[0.15] text-amber-400"
        )}
      >
        {approved ? "Approved" : "Needs Revision"}
      </span>
      <span className="text-xs text-white/40">Score: {score}/10</span>
    </div>
  );
}

interface IssueListProps {
  issues: string[];
  suggestions: string[];
}

export function IssueList({ issues, suggestions }: IssueListProps) {
  if (!issues.length && !suggestions.length) return null;
  return (
    <div className="mt-4 space-y-3">
      {issues.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold text-red-400">Issues</p>
          <ul className="space-y-1">
            {issues.map((issue, i) => (
              <li key={i} className="flex gap-2 text-xs text-white/60">
                <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-red-400" />
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}
      {suggestions.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold text-brand-400">Suggestions</p>
          <ul className="space-y-1">
            {suggestions.map((s, i) => (
              <li key={i} className="flex gap-2 text-xs text-white/60">
                <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand-400" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
