/**
 * RecentProjects — the user's most recently updated projects.
 *
 * Compact list optimised for a glance: name, status, and relative time, each
 * row linking to the project detail page. Shows skeletons while loading and a
 * friendly empty state with a CTA when the user has no projects yet.
 */

import Link from "next/link";
import { FolderOpen, Plus } from "lucide-react";

import {
  DashboardSection,
  SectionEmpty,
  SkeletonRow,
} from "@/components/features/dashboard/DashboardSection";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { timeAgo, truncate } from "@/lib/utils";
import type { Project } from "@/types/models";

interface RecentProjectsProps {
  projects?: Project[];
  loading?: boolean;
}

export function RecentProjects({ projects, loading }: RecentProjectsProps) {
  return (
    <DashboardSection
      title="Recent Projects"
      icon={FolderOpen}
      action={{ label: "View all", href: "/dashboard/projects" }}
    >
      {loading ? (
        <ul className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <li
              key={i}
              className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/2 p-3"
            >
              <div className="skeleton h-9 w-9 flex-shrink-0 rounded-md" />
              <div className="flex-1 space-y-2">
                <SkeletonRow className="h-3.5 w-1/2" />
                <SkeletonRow className="h-3 w-1/4" />
              </div>
            </li>
          ))}
        </ul>
      ) : !projects || projects.length === 0 ? (
        <SectionEmpty
          icon={FolderOpen}
          title="No projects yet"
          description="Create your first project to organise your generated media."
        />
      ) : (
        <ul className="space-y-2">
          {projects.slice(0, 5).map((project) => (
            <li key={project.id}>
              <Link
                href={`/dashboard/projects/${project.id}`}
                className="group flex items-center gap-3 rounded-lg border border-white/5 bg-white/2 p-3 transition-all hover:border-white/10 hover:bg-white/5"
              >
                <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md bg-brand-600/15 text-brand-400">
                  <FolderOpen className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-white">
                    {project.name}
                  </span>
                  <span className="block truncate text-xs text-white/40">
                    {project.description
                      ? truncate(project.description, 48)
                      : `Updated ${timeAgo(project.updated_at)}`}
                  </span>
                </span>
                <StatusBadge status={project.status} className="flex-shrink-0" />
              </Link>
            </li>
          ))}
        </ul>
      )}

      {!loading && projects && projects.length > 0 && (
        <Link
          href="/dashboard/projects"
          className="btn-ghost mt-3 w-full text-xs"
        >
          <Plus className="h-3.5 w-3.5" />
          New Project
        </Link>
      )}
    </DashboardSection>
  );
}
