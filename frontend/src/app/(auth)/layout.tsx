/**
 * Auth route group layout.
 *
 * Applied to /login and /register. Renders a centered two-column layout:
 *  - Left: branding panel with gradient (hidden on mobile)
 *  - Right: the auth form
 *
 * Authenticated users are NOT redirected here — auth redirection is
 * handled inside each page or by middleware (Phase 5+).
 */

import type { Metadata } from "next";
import Link from "next/link";
import { Sparkles } from "lucide-react";

export const metadata: Metadata = {
  robots: { index: false },
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-surface">
      {/* ---- Left branding panel (desktop only) ---- */}
      <div className="relative hidden flex-1 flex-col justify-between overflow-hidden border-r border-white/5 bg-gradient-to-br from-surface-50 via-surface-100 to-surface p-12 lg:flex">
        {/* Ambient orbs */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-20 top-20 h-72 w-72 rounded-full bg-brand-700/20 blur-[80px]" />
          <div className="absolute -bottom-20 right-0 h-96 w-96 rounded-full bg-violet-700/15 blur-[100px]" />
        </div>

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-violet-600 shadow-glow-sm">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Prabhu AI Studio</p>
            <p className="text-xs text-white/30">Local-first AI video generation</p>
          </div>
        </div>

        {/* Feature list */}
        <div className="relative space-y-4">
          <h2 className="text-2xl font-bold text-white">
            Create videos with AI
          </h2>
          <p className="max-w-xs text-sm leading-relaxed text-white/50">
            Generate complete videos from text prompts. All AI models run
            locally — your data never leaves your machine.
          </p>

          <ul className="mt-6 space-y-3">
            {[
              "Stable Diffusion image generation",
              "Piper TTS voice narration",
              "Whisper speech-to-text",
              "FFmpeg video assembly",
            ].map((feature) => (
              <li key={feature} className="flex items-center gap-3 text-sm text-white/60">
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-brand-600/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-400" />
                </span>
                {feature}
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <p className="relative text-xs text-white/20">
          100% local · No cloud · Complete privacy
        </p>
      </div>

      {/* ---- Right: form area ---- */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        {/* Mobile logo */}
        <div className="mb-8 flex items-center gap-2 lg:hidden">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-600">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-bold text-white">Prabhu AI Studio</span>
        </div>

        <div className="w-full max-w-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
