/**
 * DashboardSection — shared container for dashboard panels.
 *
 * WHY: Recent Projects, Generated Videos, and the Activity Timeline all share
 * the same "surface card + header + optional 'view all' link" chrome. Centralise
 * it here so the panels stay visually consistent and focus on their content.
 */

import Link from "next/link";
import { ArrowRight, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface DashboardSectionProps {
  title: string;
  icon: LucideIcon;
  /** Optional "view all" link rendered in the header. */
  action?: { label: string; href: string };
  /** Optional element rendered on the right of the header (e.g. a badge). */
  headerAside?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

export function DashboardSection({
  title,
  icon: Icon,
  action,
  headerAside,
  className,
  children,
}: DashboardSectionProps) {
  return (
    <section className={cn("surface-card flex flex-col p-5", className)}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-brand-400" />
          <h2 className="text-sm font-semibold text-white">{title}</h2>
        </div>

        {headerAside}

        {action && (
          <Link
            href={action.href}
            className="group inline-flex items-center gap-1 text-xs font-medium text-white/40 transition-colors hover:text-brand-300"
          >
            {action.label}
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        )}
      </div>

      <div className="flex-1">{children}</div>
    </section>
  );
}

/** Inline empty-state used inside dashboard panels. */
export function SectionEmpty({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-white/8 bg-white/2 px-4 py-10 text-center">
      <Icon className="mb-3 h-8 w-8 text-white/12" />
      <p className="text-sm font-medium text-white/80">{title}</p>
      <p className="mt-1 max-w-xs text-xs text-white/40">{description}</p>
    </div>
  );
}

/** Simple pulsing skeleton line for loading states. */
export function SkeletonRow({ className }: { className?: string }) {
  return <div className={cn("skeleton h-4 w-full", className)} />;
}
