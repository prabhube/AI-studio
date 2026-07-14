"use client";

/**
 * Application top header bar.
 *
 * Renders:
 *  - Mobile: hamburger button (opens the mobile drawer) + logo
 *  - Desktop: page title + breadcrumbs
 *  - Right side: live system health badge, notification bell
 *
 * The page title and breadcrumbs are driven by the UI store so any
 * page component can call setPageTitle() without prop-drilling.
 */

import { Menu, ChevronRight, LogOut, User } from "lucide-react";
import Link from "next/link";

import { useUIStore } from "@/store/ui-store";
import {
  useSystemHealth,
  deriveOverallStatus,
  STATUS_COLORS,
  STATUS_LABELS,
} from "@/hooks/useSystemHealth";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// System health badge
// ---------------------------------------------------------------------------

function SystemHealthBadge() {
  const { data, isError, isLoading } = useSystemHealth();
  const status = deriveOverallStatus(data, isError);

  return (
    <div
      className="flex items-center gap-2 rounded-full border border-white/6 bg-white/4 px-3 py-1.5"
      title={
        data
          ? `DB: ${data.services.postgres.latency_ms?.toFixed(0) ?? "—"}ms · Redis: ${data.services.redis.latency_ms?.toFixed(0) ?? "—"}ms`
          : "Checking system health…"
      }
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full transition-colors",
          isLoading ? "animate-pulse bg-white/20" : STATUS_COLORS[status]
        )}
      />
      <span className="hidden text-xs text-white/50 sm:block">
        {isLoading ? "Checking…" : STATUS_LABELS[status]}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Breadcrumbs
// ---------------------------------------------------------------------------

interface Crumb {
  label: string;
  href?: string;
}

function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  if (crumbs.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="hidden items-center gap-1 sm:flex">
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1;
        return (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && (
              <ChevronRight className="h-3.5 w-3.5 flex-shrink-0 text-white/20" />
            )}
            {crumb.href && !isLast ? (
              <Link
                href={crumb.href}
                className="text-sm text-white/40 transition-colors hover:text-white/70"
              >
                {crumb.label}
              </Link>
            ) : (
              <span
                className={cn(
                  "text-sm",
                  isLast ? "font-medium text-white" : "text-white/40"
                )}
              >
                {crumb.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}

// ---------------------------------------------------------------------------
// TopBar
// ---------------------------------------------------------------------------

export function TopBar() {
  const { pageTitle, pageBreadcrumbs, setMobileMenuOpen } = useUIStore();

  return (
    <header
      className="flex h-[60px] flex-shrink-0 items-center justify-between border-b border-white/5 bg-surface-50 px-4 md:px-6"
      role="banner"
    >
      {/* Left — mobile hamburger + title / breadcrumbs */}
      <div className="flex min-w-0 flex-1 items-center gap-3">
        {/* Mobile: hamburger */}
        <button
          onClick={() => setMobileMenuOpen(true)}
          aria-label="Open navigation menu"
          className="btn-icon flex-shrink-0 md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Desktop: page title or breadcrumbs */}
        {pageBreadcrumbs.length > 0 ? (
          <Breadcrumbs crumbs={pageBreadcrumbs} />
        ) : (
          <h1 className="truncate text-sm font-semibold text-white">
            {pageTitle}
          </h1>
        )}
      </div>

      {/* Right — health badge + user avatar */}
      <div className="ml-4 flex flex-shrink-0 items-center gap-2.5">
        <SystemHealthBadge />
        <TopBarUserMenu />
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// User menu in TopBar (avatar + quick logout)
// ---------------------------------------------------------------------------

function TopBarUserMenu() {
  const { user, logout } = useAuth();

  if (!user) return null;

  const initials = (user.full_name ?? user.username)
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="flex items-center gap-2">
      <Link
        href="/dashboard/settings"
        className="flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-white/5"
        title="Your profile"
      >
        {user.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.avatar_url}
            alt={user.full_name ?? user.username}
            className="h-7 w-7 rounded-full object-cover ring-1 ring-white/10"
          />
        ) : (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/25 text-xs font-semibold text-brand-300">
            {initials}
          </div>
        )}
        <span className="hidden text-xs text-white/60 lg:block">
          {user.full_name ?? user.username}
        </span>
      </Link>

      <button
        onClick={() => void logout()}
        aria-label="Sign out"
        title="Sign out"
        className="btn-icon"
      >
        <LogOut className="h-4 w-4" />
      </button>
    </div>
  );
}
