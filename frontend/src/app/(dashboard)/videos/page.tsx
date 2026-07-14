"use client";

import { useEffect } from "react";
import { Video, Sparkles } from "lucide-react";
import { useUIStore } from "@/store/ui-store";
import { Button } from "@/components/ui/button";

export default function VideosPage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();

  useEffect(() => {
    setPageTitle("Videos");
    setPageBreadcrumbs([
      { label: "Dashboard", href: "/dashboard" },
      { label: "Videos" },
    ]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Videos</h1>
          <p className="section-subtitle">
            Generate full videos from text prompts using the AI pipeline.
          </p>
        </div>
        <Button variant="primary" size="sm">
          <Sparkles className="h-4 w-4" />
          Generate Video
        </Button>
      </div>

      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/8 bg-white/2 py-24">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-600/10">
          <Video className="h-7 w-7 text-brand-500" />
        </div>
        <h3 className="mb-2 text-base font-semibold text-white">
          No videos yet
        </h3>
        <p className="mb-6 max-w-xs text-center text-sm text-white/40">
          Describe your video in a text prompt and let the local AI models
          create it for you.
        </p>
        <Button variant="primary" size="sm">
          <Sparkles className="h-4 w-4" />
          Generate Your First Video
        </Button>
      </div>
    </div>
  );
}
