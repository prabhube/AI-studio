import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const spinnerVariants = cva("animate-spin rounded-full border-2", {
  variants: {
    size: {
      xs: "h-3 w-3",
      sm: "h-4 w-4",
      md: "h-6 w-6 border-[3px]",
      lg: "h-8 w-8 border-[3px]",
      xl: "h-12 w-12 border-4",
    },
    variant: {
      brand:  "border-brand-700 border-t-brand-400",
      white:  "border-white/20 border-t-white",
      muted:  "border-white/10 border-t-white/40",
    },
  },
  defaultVariants: {
    size: "md",
    variant: "brand",
  },
});

export interface SpinnerProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof spinnerVariants> {
  label?: string;
}

export function Spinner({ className, size, variant, label = "Loading…", ...props }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn(spinnerVariants({ size, variant }), className)}
      {...props}
    />
  );
}

/** Full-page loading state */
export function PageSpinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <Spinner size="lg" />
      <p className="animate-pulse text-sm text-white/40">{label}</p>
    </div>
  );
}
