"use client";

import { useEffect } from "react";
import { Image, Sparkles } from "lucide-react";
import { useUIStore } from "@/store/ui-store";
import { Button } from "@/components/ui/button";

export default function ImagesPage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();

  useEffect(() => {
    setPageTitle("Images");
    setPageBreadcrumbs([
      { label: "Dashboard", href: "/dashboard" },
      { label: "Images" },
    ]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Image Gallery</h1>
          <p className="section-subtitle">
            AI-generated frames and standalone images from Stable Diffusion.
          </p>
        </div>
        <Button variant="primary" size="sm">
          <Sparkles className="h-4 w-4" />
          Generate Image
        </Button>
      </div>

      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/8 bg-white/2 py-24">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-600/10">
          <Image className="h-7 w-7 text-brand-500" />
        </div>
        <h3 className="mb-2 text-base font-semibold text-white">
          No images yet
        </h3>
        <p className="mb-6 max-w-xs text-center text-sm text-white/40">
          Generate images using Stable Diffusion running locally on your
          hardware. No cloud. No limits.
        </p>
        <Button variant="primary" size="sm">
          <Sparkles className="h-4 w-4" />
          Generate First Image
        </Button>
      </div>
    </div>
  );
}
