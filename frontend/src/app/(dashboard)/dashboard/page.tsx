"use client";

/**
 * Dashboard home page.
 *
 * Shows:
 *  - System health cards (DB, Redis, disk)
 *  - Quick-action buttons (create project, generate video, etc.)
 *  - Recent activity placeholder (populated in Phase 3+)
 *  - Getting started guide when no projects exist
 */

import { useEffect } from "react";
import {
  Video,
  Image,
  Mic,
  FolderPlus,
  Cpu,
  Database,
  HardDrive,
  Zap,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";

import { useUIStore } from "@/store/ui-store";
import { useSystemHealth, deriveOverallStatus } from "@/hooks/useSystemHealth";
import { StatCard } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Quick actions
// ---------------------------------------------------------------------------

const QUICK_ACTIONS = [
  {
    label: "New Project",
    description: "Start a complete video pipeline",
    href: "/dashboard/projects",
    icon: FolderPlus,
    variant: "primary" as const,
  },
  {
    label: "Generate Video",
    description: "Text prompt → full video",
    href: "/dashboard/videos",
    icon: Video,
    variant: "secondary" as const,
  },
  {
    label: "Generate Image",
    description: "Stable Diffusion locally",
    href: "/dashboard/images",
    icon: Image,
    variant: "secondary" as const,
  },
  {
    label: "Voice Studio",
    description: "TTS narration · STT transcription",
    href: "/dashboard/voice",
    icon: Mic,
    variant: "secondary" as const,
  },
];

// ---------------------------------------------------------------------------
// System status panel
// ---------------------------------------------------------------------------

function SystemStatusPanel() {
  const { data, isLoading, isError } = useSystemHealth();
  const status = deriveOverallStatus(data, isError);

  const postgres = data?.services.postgres;
  const redis = data?.services.redis;

  const statusVariant = {
    healthy: "success",
    degraded: "warning",
    unhealthy: "danger",
    unknown: "default",
  } as const;

  return (
    <div className="surface-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Infrastructure</h2>
        {isLoading ? (
          <Spinner size="xs" variant="muted" />
        ) : (
          <Badge variant={statusVariant[status]}>
            {status === "healthy" ? "All Systems Operational" :
             status === "degraded" ? "Degraded" :
             status === "unhealthy" ? "Service Issue" : "Checking…"}
          </Badge>
        )}
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {/* PostgreSQL */}
        <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/3 p-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-sky-500/10">
            <Database className="h-4 w-4 text-sky-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">PostgreSQL</p>
            <p className="text-xs text-white/40">
              {isLoading ? "…" :
               postgres?.status === "ok"
                 ? `${postgres.latency_ms?.toFixed(0) ?? "—"}ms`
                 : "Unavailable"}
            </p>
          </div>
          <span
            className={cn(
              "ml-auto h-2 w-2 flex-shrink-0 rounded-full",
              isLoading ? "bg-white/20 animate-pulse" :
              postgres?.status === "ok" ? "bg-emerald-400" : "bg-red-400"
            )}
          />
        </div>

        {/* Redis */}
        <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/3 p-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-red-500/10">
            <Cpu className="h-4 w-4 text-red-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">Redis</p>
            <p className="text-xs text-white/40">
              {isLoading ? "…" :
               redis?.status === "ok"
                 ? `${redis.latency_ms?.toFixed(0) ?? "—"}ms`
                 : "Unavailable"}
            </p>
          </div>
          <span
            className={cn(
              "ml-auto h-2 w-2 flex-shrink-0 rounded-full",
              isLoading ? "bg-white/20 animate-pulse" :
              redis?.status === "ok" ? "bg-emerald-400" : "bg-amber-400"
            )}
          />
        </div>

        {/* Disk */}
        <div className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/3 p-3">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-violet-500/10">
            <HardDrive className="h-4 w-4 text-violet-400" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">Disk</p>
            <p className="text-xs text-white/40">
              {isLoading ? "…" :
               data?.disk?.free_gb != null
                 ? `${data.disk.free_gb.toFixed(1)} GB free`
                 : "N/A"}
            </p>
          </div>
          <span
            className={cn(
              "ml-auto h-2 w-2 flex-shrink-0 rounded-full",
              isLoading ? "bg-white/20 animate-pulse" :
              data?.disk?.percent_used != null && data.disk.percent_used > 90
                ? "bg-red-400"
                : "bg-emerald-400"
            )}
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Getting started
// ---------------------------------------------------------------------------

function GettingStarted() {
  const steps = [
    {
      number: "01",
      title: "Configure AI Models",
      description: "Set LLM_PROVIDER, IMAGE_PROVIDER, TTS_PROVIDER in your .env file.",
      href: "/dashboard/settings",
      done: false,
    },
    {
      number: "02",
      title: "Create a Project",
      description: "Projects organise your videos, images, and audio clips.",
      href: "/dashboard/projects",
      done: false,
    },
    {
      number: "03",
      title: "Generate Your First Video",
      description: "Enter a text prompt and let the AI pipeline do the rest.",
      href: "/dashboard/videos",
      done: false,
    },
  ];

  return (
    <div className="surface-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Zap className="h-4 w-4 text-brand-400" />
        <h2 className="text-sm font-semibold text-white">Getting Started</h2>
      </div>
      <div className="space-y-3">
        {steps.map((step) => (
          <Link
            key={step.number}
            href={step.href}
            className="flex items-start gap-4 rounded-lg p-3 transition-all hover:bg-white/4"
          >
            <span className="mt-0.5 flex-shrink-0 font-mono text-xs font-bold text-brand-600">
              {step.number}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white">{step.title}</p>
              <p className="text-xs text-white/40">{step.description}</p>
            </div>
            <ArrowRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-white/20 transition-colors group-hover:text-white/50" />
          </Link>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const { setPageTitle, setPageBreadcrumbs } = useUIStore();

  useEffect(() => {
    setPageTitle("Dashboard");
    setPageBreadcrumbs([{ label: "Dashboard" }]);
  }, [setPageTitle, setPageBreadcrumbs]);

  return (
    <div className="animate-fade-in space-y-6">
      {/* Page heading */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-white/40">
          Local-first AI video generation — all processing runs on your machine.
        </p>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Projects" value="0" icon={<FolderPlus className="h-5 w-5" />} />
        <StatCard label="Videos Generated" value="0" icon={<Video className="h-5 w-5" />} />
        <StatCard label="Images Generated" value="0" icon={<Image className="h-5 w-5" />} />
        <StatCard label="Audio Clips" value="0" icon={<Mic className="h-5 w-5" />} />
      </div>

      {/* Two-column layout: quick actions + system status */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Quick actions — wider column */}
        <div className="space-y-4 lg:col-span-3">
          <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider">
            Quick Actions
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {QUICK_ACTIONS.map((action) => (
              <Link
                key={action.href}
                href={action.href}
                className="glass-card-hover group flex flex-col gap-3 p-5"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/15 transition-colors group-hover:bg-brand-600/25">
                  <action.icon className="h-5 w-5 text-brand-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">
                    {action.label}
                  </p>
                  <p className="mt-0.5 text-xs text-white/40">
                    {action.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Right column — system status + getting started */}
        <div className="space-y-4 lg:col-span-2">
          <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider">
            System
          </h2>
          <SystemStatusPanel />
          <GettingStarted />
        </div>
      </div>
    </div>
  );
}
