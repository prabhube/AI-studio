import * as React from "react";
import { cn } from "@/lib/utils";

// ---- Card root ----
const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { hover?: boolean }
>(({ className, hover, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border border-white/6 bg-surface-50",
      hover && "transition-all duration-200 hover:border-white/10 hover:bg-surface-100 cursor-pointer",
      className
    )}
    {...props}
  />
));
Card.displayName = "Card";

// ---- Card header ----
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1 p-6 pb-4", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

// ---- Card title ----
const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("text-base font-semibold leading-none text-white", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

// ---- Card description ----
const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-white/45", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

// ---- Card content ----
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

// ---- Card footer ----
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

// ---- Stat card ----
interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  delta?: { value: string; positive: boolean };
  className?: string;
}

function StatCard({ label, value, icon, delta, className }: StatCardProps) {
  return (
    <Card className={cn("p-5", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-white/40 uppercase tracking-wider">
            {label}
          </p>
          <p className="mt-2 text-2xl font-bold text-white">{value}</p>
          {delta && (
            <p
              className={cn(
                "mt-1 text-xs font-medium",
                delta.positive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {delta.positive ? "↑" : "↓"} {delta.value}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand-600/15 text-brand-400">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  StatCard,
};
