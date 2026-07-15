/**
 * QuickGenerate — one-click entry point to the generation pipelines.
 *
 * WHY a dropdown instead of a single button?
 *   The studio produces videos, images, and voice. A single "Quick Generate"
 *   affordance that fans out to each pipeline keeps the primary action obvious
 *   while avoiding a row of competing buttons in the page header.
 *
 * The primary click targets Video (the flagship pipeline); the caret opens the
 * full menu. Built on Radix DropdownMenu for accessibility (keyboard nav, focus
 * trapping, ARIA) out of the box.
 */

"use client";

import { useRouter } from "next/navigation";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { ChevronDown, Image, Mic, Sparkles, Video } from "lucide-react";
import { cn } from "@/lib/utils";

interface GenerateOption {
  label: string;
  description: string;
  href: string;
  icon: typeof Video;
}

const OPTIONS: GenerateOption[] = [
  {
    label: "Video",
    description: "Text prompt → full video",
    href: "/dashboard/videos",
    icon: Video,
  },
  {
    label: "Image",
    description: "Stable Diffusion locally",
    href: "/dashboard/images",
    icon: Image,
  },
  {
    label: "Voice",
    description: "TTS narration & transcription",
    href: "/dashboard/voice",
    icon: Mic,
  },
];

export function QuickGenerate({ className }: { className?: string }) {
  const router = useRouter();

  return (
    <div className={cn("inline-flex items-stretch", className)}>
      {/* Primary action — jump straight to the video pipeline */}
      <button
        type="button"
        onClick={() => router.push("/dashboard/videos")}
        className="inline-flex h-9 items-center gap-2 rounded-l-lg bg-brand-600 px-3.5 text-sm font-semibold text-white shadow-lg shadow-brand-900/30 transition-all duration-150 hover:bg-brand-500 hover:shadow-brand-800/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-surface active:scale-[0.98]"
      >
        <Sparkles className="h-4 w-4" />
        Quick Generate
      </button>

      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          <button
            type="button"
            aria-label="Choose what to generate"
            className="inline-flex h-9 items-center justify-center rounded-r-lg border-l border-brand-800/60 bg-brand-600 px-2 text-white transition-all duration-150 hover:bg-brand-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-surface active:scale-[0.98] data-[state=open]:bg-brand-500"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </DropdownMenu.Trigger>

        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            sideOffset={8}
            className="z-50 w-64 origin-top-right rounded-xl border border-white/8 bg-surface-50 p-1.5 shadow-2xl shadow-black/40 data-[state=open]:animate-fade-in"
          >
            <DropdownMenu.Label className="px-2.5 py-1.5 text-xs font-medium uppercase tracking-wider text-white/40">
              Generate
            </DropdownMenu.Label>
            {OPTIONS.map((option) => (
              <DropdownMenu.Item
                key={option.href}
                onSelect={() => router.push(option.href)}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-2.5 py-2 text-sm text-white/80 outline-none transition-colors data-[highlighted]:bg-white/6 data-[highlighted]:text-white"
              >
                <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-brand-600/15 text-brand-400">
                  <option.icon className="h-4 w-4" />
                </span>
                <span className="min-w-0">
                  <span className="block font-medium">{option.label}</span>
                  <span className="block truncate text-xs text-white/40">
                    {option.description}
                  </span>
                </span>
              </DropdownMenu.Item>
            ))}
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>
    </div>
  );
}
