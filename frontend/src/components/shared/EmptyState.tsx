/**
 * EmptyState Component.
 *
 * WHY this component exists:
 *   Consistent "no items yet" UI shown across all list views:
 *   projects, videos, images, audio clips.
 *   Includes a call-to-action button to create the first item.
 */

import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="glass-card flex flex-col items-center justify-center py-20 text-center">
      <Icon className="mb-4 h-14 w-14 text-white/10" />
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-white/40">{description}</p>
      {action && (
        <button onClick={action.onClick} className="btn-primary mt-6">
          {action.label}
        </button>
      )}
    </div>
  );
}
