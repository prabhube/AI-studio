"use client";

import { useEffect } from "react";
import { Mic } from "lucide-react";
import { useUIStore } from "@/store/ui-store";
import { Button } from "@/components/ui/button";

export default function VoicePage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();

  useEffect(() => {
    setPageTitle("Voice Studio");
    setPageBreadcrumbs([
      { label: "Dashboard", href: "/dashboard" },
      { label: "Voice Studio" },
    ]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Voice Studio</h1>
          <p className="section-subtitle">
            Text-to-speech with Piper TTS · Speech-to-text with Whisper.
          </p>
        </div>
        <Button variant="primary" size="sm">
          <Mic className="h-4 w-4" />
          Synthesize Speech
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* TTS */}
        <div className="surface-card p-6">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10">
            <Mic className="h-5 w-5 text-violet-400" />
          </div>
          <h3 className="mb-1 text-sm font-semibold text-white">
            Text to Speech
          </h3>
          <p className="text-xs text-white/40">
            Convert text to natural audio narration using Piper TTS running
            locally.
          </p>
          <Button variant="secondary" size="sm" className="mt-4">
            Open TTS
          </Button>
        </div>

        {/* STT */}
        <div className="surface-card p-6">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10">
            <Mic className="h-5 w-5 text-sky-400" />
          </div>
          <h3 className="mb-1 text-sm font-semibold text-white">
            Speech to Text
          </h3>
          <p className="text-xs text-white/40">
            Transcribe audio or video files using Whisper locally — no cloud
            upload.
          </p>
          <Button variant="secondary" size="sm" className="mt-4">
            Open STT
          </Button>
        </div>
      </div>
    </div>
  );
}
