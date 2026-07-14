/**
 * ProjectCard Component — Placeholder.
 *
 * WHY this component exists:
 *   Displays a single project in the grid on /projects.
 *   Shows: project name, description, status badge, asset counts,
 *   last updated time, and action menu (rename, delete).
 *
 * Props:
 *   project  — Project object from the API
 *   onDelete — Callback when user confirms deletion
 *
 * Implementation: Phase 2.
 */

import type { Project } from "@/types/models";

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
}

export function ProjectCard({ project, onDelete }: ProjectCardProps) {
  return (
    <div className="glass-card p-5">
      <p className="font-semibold text-white">{project.name}</p>
      <p className="mt-1 text-xs text-white/30">Status: {project.status}</p>
      <p className="mt-4 text-xs text-white/20">ProjectCard — Phase 2</p>
    </div>
  );
}
