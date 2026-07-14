"use client";

import { useEffect } from "react";
import { Settings, Cpu, Database, Layers, Server } from "lucide-react";
import { useUIStore } from "@/store/ui-store";
import { Badge } from "@/components/ui/badge";
import { env } from "@/env";

interface ConfigRow {
  label: string;
  envKey: string;
  description: string;
  exampleValue: string;
}

const AI_CONFIG_ROWS: ConfigRow[] = [
  {
    label: "LLM Provider",
    envKey: "LLM_PROVIDER",
    description: "Language model for script generation",
    exampleValue: "gemma | llama | none",
  },
  {
    label: "Image Provider",
    envKey: "IMAGE_PROVIDER",
    description: "Image generation model",
    exampleValue: "stable_diffusion | none",
  },
  {
    label: "TTS Provider",
    envKey: "TTS_PROVIDER",
    description: "Text-to-speech engine",
    exampleValue: "piper | none",
  },
  {
    label: "STT Provider",
    envKey: "STT_PROVIDER",
    description: "Speech-to-text engine",
    exampleValue: "whisper | none",
  },
  {
    label: "Video Provider",
    envKey: "VIDEO_PROVIDER",
    description: "Video assembly tool",
    exampleValue: "ffmpeg | none",
  },
];

export default function SettingsPage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();

  useEffect(() => {
    setPageTitle("Settings");
    setPageBreadcrumbs([
      { label: "Dashboard", href: "/dashboard" },
      { label: "Settings" },
    ]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="section-title">Settings</h1>
        <p className="section-subtitle">
          Application configuration and AI model setup.
        </p>
      </div>

      {/* App Info */}
      <div className="surface-card divide-y divide-white/5">
        <div className="flex items-center gap-3 p-5">
          <Server className="h-5 w-5 text-brand-400" />
          <h2 className="text-sm font-semibold text-white">Application</h2>
        </div>
        <div className="grid gap-px sm:grid-cols-2">
          {[
            { label: "Version", value: env.appVersion },
            { label: "Environment", value: env.nodeEnv },
            { label: "API URL", value: env.apiUrl },
            { label: "Health Poll", value: `${env.healthPollIntervalMs / 1000}s` },
          ].map(({ label, value }) => (
            <div key={label} className="p-4">
              <p className="text-xs text-white/40">{label}</p>
              <p className="mt-0.5 font-mono text-sm text-white">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* AI Providers */}
      <div className="surface-card divide-y divide-white/5">
        <div className="flex items-center gap-3 p-5">
          <Cpu className="h-5 w-5 text-violet-400" />
          <div>
            <h2 className="text-sm font-semibold text-white">AI Providers</h2>
            <p className="text-xs text-white/40">
              Configure via environment variables in your .env file
            </p>
          </div>
        </div>
        {AI_CONFIG_ROWS.map((row) => (
          <div
            key={row.envKey}
            className="flex flex-col gap-1 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-white">{row.label}</p>
                <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-xs text-white/40">
                  {row.envKey}
                </code>
              </div>
              <p className="mt-0.5 text-xs text-white/40">{row.description}</p>
            </div>
            <Badge variant="default" className="shrink-0 font-mono">
              {row.exampleValue}
            </Badge>
          </div>
        ))}
      </div>

      {/* Note */}
      <div className="rounded-lg border border-brand-500/20 bg-brand-500/5 p-4">
        <div className="flex items-start gap-3">
          <Layers className="mt-0.5 h-4 w-4 flex-shrink-0 text-brand-400" />
          <div>
            <p className="text-sm font-medium text-brand-300">
              Configuration via .env file
            </p>
            <p className="mt-1 text-xs text-brand-400/70">
              All settings are loaded from the backend <code>.env</code> file.
              Changes require a container restart. See{" "}
              <code>.env.example</code> for all available options.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
