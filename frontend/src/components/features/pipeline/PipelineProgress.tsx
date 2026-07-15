"use client";

import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { PIPELINE_STEPS, type PipelineStep } from "@/types/pipeline";

interface PipelineProgressProps {
  currentStep: PipelineStep;
  completedSteps: Set<PipelineStep>;
  loadingStep: PipelineStep | null;
}

export function PipelineProgress({
  currentStep,
  completedSteps,
  loadingStep,
}: PipelineProgressProps) {
  return (
    <div className="w-full overflow-x-auto pb-2">
      <div className="flex min-w-max items-center gap-0">
        {PIPELINE_STEPS.map((step, idx) => {
          const isCompleted = completedSteps.has(step.key);
          const isCurrent = currentStep === step.key;
          const isLoading = loadingStep === step.key;
          const isPending = !isCompleted && !isCurrent;

          return (
            <div key={step.key} className="flex items-center">
              {/* Step circle */}
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={cn(
                    "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all",
                    isCompleted && "bg-emerald-500 text-white",
                    isCurrent && !isLoading && "bg-brand-600 text-white ring-2 ring-brand-400 ring-offset-2 ring-offset-surface",
                    isLoading && "bg-brand-600 text-white",
                    isPending && "border border-white/[0.12] bg-white/[0.04] text-white/30"
                  )}
                >
                  {isLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : isCompleted ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : (
                    step.step
                  )}
                </div>
                <span
                  className={cn(
                    "max-w-[72px] text-center text-[10px] leading-tight",
                    isCompleted && "text-emerald-400",
                    isCurrent && "font-semibold text-white",
                    isPending && "text-white/30"
                  )}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {idx < PIPELINE_STEPS.length - 1 && (
                <div
                  className={cn(
                    "mx-1 mt-[-18px] h-px w-8 flex-shrink-0 transition-all",
                    isCompleted ? "bg-emerald-500/50" : "bg-white/[0.08]"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
