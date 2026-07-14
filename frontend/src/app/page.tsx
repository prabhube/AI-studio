import Link from "next/link";
import { Sparkles, Video, Mic, Image, Zap, ArrowRight, Shield } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Prabhu AI Studio — Local-First AI Video Generation",
};

const FEATURES = [
  {
    icon: Sparkles,
    title: "Prompt to Video",
    description:
      "Describe your vision in plain English. The LLM understands and plans your full video production pipeline.",
  },
  {
    icon: Image,
    title: "AI Image Generation",
    description:
      "Stable Diffusion generates stunning frames based on your script — running locally on your own GPU or CPU.",
  },
  {
    icon: Mic,
    title: "Voice Narration",
    description:
      "Piper TTS creates natural-sounding narration. Whisper STT transcribes your own voice recordings.",
  },
  {
    icon: Video,
    title: "FFmpeg Assembly",
    description:
      "Professional video assembly with transitions, audio sync, and subtitle support — fully automated.",
  },
];

const TECH_STACK = [
  "Llama / Gemma",
  "Stable Diffusion",
  "Piper TTS",
  "Whisper STT",
  "FFmpeg",
  "FastAPI",
  "Next.js 15",
  "PostgreSQL",
];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-surface">
      {/* Ambient gradient background */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-brand-700/15 blur-[100px]" />
        <div className="absolute -right-40 top-1/3 h-[500px] w-[500px] rounded-full bg-violet-700/10 blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-pink-700/8 blur-[80px]" />
      </div>

      <div className="relative mx-auto max-w-6xl px-6 py-20">
        {/* ---- Hero ---- */}
        <div className="flex flex-col items-center text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-brand-500/8 px-4 py-1.5 text-sm text-brand-300">
            <Sparkles className="h-3.5 w-3.5" />
            Local-First AI Video Studio
          </div>

          <h1 className="mb-6 text-balance text-5xl font-extrabold tracking-tight text-white sm:text-6xl lg:text-7xl">
            Create Videos with{" "}
            <span className="gradient-text">AI Magic</span>
          </h1>

          <p className="mb-10 max-w-2xl text-balance text-lg text-white/55">
            Transform text prompts into complete videos using open-source AI
            models — all running locally on your machine. No cloud. No
            subscriptions. Complete privacy.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="btn-primary px-7 py-3 text-base"
            >
              Open Studio
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="https://github.com/prabhu-ai-studio"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary px-7 py-3 text-base"
            >
              View on GitHub
            </a>
          </div>

          {/* Privacy callout */}
          <div className="mt-6 flex items-center gap-2 text-sm text-white/30">
            <Shield className="h-3.5 w-3.5" />
            100% local processing — your data never leaves your machine
          </div>
        </div>

        {/* ---- Feature grid ---- */}
        <div className="mt-24 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="glass-card p-6">
              <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600/15">
                <feature.icon className="h-5 w-5 text-brand-400" />
              </div>
              <h3 className="mb-2 font-semibold text-white">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-white/45">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* ---- Tech stack ---- */}
        <div className="mt-24 text-center">
          <p className="mb-8 text-xs font-semibold uppercase tracking-widest text-white/25">
            Powered by open-source AI
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 text-white/35">
            {TECH_STACK.map((tech) => (
              <span
                key={tech}
                className="rounded-lg border border-white/5 bg-white/4 px-4 py-2 text-sm font-medium"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* ---- CTA ---- */}
        <div className="mt-24 flex flex-col items-center">
          <div className="glass-card max-w-xl p-8 text-center">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600/20">
              <Zap className="h-6 w-6 text-brand-400" />
            </div>
            <h2 className="mb-3 text-xl font-bold text-white">
              Ready to generate your first video?
            </h2>
            <p className="mb-6 text-sm text-white/45">
              Open the studio, create a project, and start with a text prompt.
              The entire AI pipeline runs on your hardware.
            </p>
            <Link href="/dashboard" className="btn-primary px-6 py-2.5">
              Launch Studio
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
