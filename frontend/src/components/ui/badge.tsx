import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default:  "bg-white/8 text-white/60",
        primary:  "bg-brand-500/15 text-brand-300",
        success:  "bg-emerald-500/15 text-emerald-300",
        warning:  "bg-amber-500/15 text-amber-300",
        danger:   "bg-red-500/15 text-red-300",
        info:     "bg-sky-500/15 text-sky-300",
        purple:   "bg-violet-500/15 text-violet-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
