"use client";

import { useEffect } from "react";
import { FolderOpen, Plus } from "lucide-react";
import { useUIStore } from "@/store/ui-store";
import { Button } from "@/components/ui/button";

export default function ProjectsPage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();

  useEffect(() => {
    setPageTitle("Projects");
    setPageBreadcrumbs([
      { label: "Dashboard", href: "/dashboard" },
      { label: "Projects" },
    ]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Projects</h1>
          <p className="section-subtitle">
            Organise your AI-generated videos, images, and audio clips.
          </p>
        </div>
        <Button variant="primary" size="sm">
          <Plus className="h-4 w-4" />
          New Project
        </Button>
      </div>

      {/* Empty state */}
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/8 bg-white/2 py-24">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-600/10">
          <FolderOpen className="h-7 w-7 text-brand-500" />
        </div>
        <h3 className="mb-2 text-base font-semibold text-white">
          No projects yet
        </h3>
        <p className="mb-6 max-w-xs text-center text-sm text-white/40">
          Create your first project to start generating AI videos and organising
          your media assets.
        </p>
        <Button variant="primary" size="sm">
          <Plus className="h-4 w-4" />
          Create Project
        </Button>
      </div>
    </div>
  );
}
