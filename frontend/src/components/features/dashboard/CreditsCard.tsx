/**
 * CreditsCard — the user's generation-credit balance and plan.
 *
 * Shows available balance, how much of the monthly allowance is used, the
 * current plan, and a shortcut to top up. Degrades gracefully to a skeleton
 * while loading and to a neutral empty state if billing data is unavailable.
 */

import Link from "next/link";
import { Coins, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ProgressBar } from "@/components/shared/ProgressBar";
import { SkeletonRow } from "@/components/features/dashboard/DashboardSection";
import { clamp, formatDate, formatNumber } from "@/lib/utils";
import type { CreditsBalance } from "@/types/dashboard";

interface CreditsCardProps {
  credits?: CreditsBalance;
  loading?: boolean;
}

export function CreditsCard({ credits, loading }: CreditsCardProps) {
  return (
    <div className="surface-card flex flex-col p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Coins className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-white">Credits</h2>
        </div>
        {credits && !loading && (
          <Badge variant="primary">{credits.plan} plan</Badge>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          <SkeletonRow className="h-9 w-32" />
          <SkeletonRow className="h-1.5" />
          <SkeletonRow className="h-8" />
        </div>
      ) : credits ? (
        <CreditsBody credits={credits} />
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center py-6 text-center">
          <p className="text-sm font-medium text-white/80">Credits unavailable</p>
          <p className="mt-1 text-xs text-white/40">
            Billing information could not be loaded right now.
          </p>
        </div>
      )}
    </div>
  );
}

function CreditsBody({ credits }: { credits: CreditsBalance }) {
  const { balance, monthly_allowance, used_this_month, renews_at } = credits;
  const usedPercent =
    monthly_allowance > 0
      ? clamp(Math.round((used_this_month / monthly_allowance) * 100), 0, 100)
      : 0;
  const low = monthly_allowance > 0 && balance / monthly_allowance <= 0.15;

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-3xl font-bold leading-none text-white">
            {formatNumber(balance)}
          </p>
          <p className="mt-1 text-xs text-white/40">credits available</p>
        </div>
        {low && <Badge variant="warning">Low balance</Badge>}
      </div>

      <div className="mt-5">
        <ProgressBar
          percent={usedPercent}
          label={`${formatNumber(used_this_month)} / ${formatNumber(monthly_allowance)} used`}
        />
        {renews_at && (
          <p className="mt-2 text-xs text-white/35">
            Allowance renews {formatDate(renews_at)}
          </p>
        )}
      </div>

      <Link
        href="/dashboard/settings"
        className="btn-secondary mt-5 w-full"
      >
        <Plus className="h-4 w-4" />
        Buy Credits
      </Link>
    </div>
  );
}
