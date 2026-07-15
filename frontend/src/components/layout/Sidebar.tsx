"use client";

/**
 * Application Sidebar.
 *
 * Behaviour:
 *  - Desktop: fixed left rail, width 256px (expanded) or 68px (collapsed).
 *  - Mobile (<768px): off-canvas drawer controlled by mobile menu state.
 *  - Bottom of sidebar shows current user avatar, name, and logout button.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Video,
  Image,
  Mic,
  Settings,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
  X,
  Sparkles,
  LogOut,
  User,
  Clapperboard,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui-store";
import { useAuth } from "@/hooks/useAuth";

// ---------------------------------------------------------------------------
// Navigation definition
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  exact?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    label: "Create Video",
    href: "/dashboard/create",
    icon: Clapperboard,
    badge: "AI",
  },
  {
    label: "Projects",
    href: "/dashboard/projects",
    icon: FolderOpen,
  },
  {
    label: "Videos",
    href: "/dashboard/videos",
    icon: Video,
  },
  {
    label: "Images",
    href: "/dashboard/images",
    icon: Image,
  },
  {
    label: "Voice Studio",
    href: "/dashboard/voice",
    icon: Mic,
  },
  {
    label: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface NavLinkProps {
  item: NavItem;
  collapsed: boolean;
  onClick?: () => void;
}

function NavLink({ item, collapsed, onClick }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = item.exact
    ? pathname === item.href
    : pathname.startsWith(item.href);

  return (
    <Link
      href={item.href}
      onClick={onClick}
      title={collapsed ? item.label : undefined}
      className={cn(
        "nav-item group relative",
        isActive ? "nav-item-active" : "nav-item-inactive",
        collapsed && "justify-center px-0"
      )}
    >
      <item.icon
        className={cn(
          "h-4 w-4 flex-shrink-0 transition-colors",
          isActive ? "text-brand-400" : "text-current"
        )}
      />
      {!collapsed && (
        <span className="truncate">{item.label}</span>
      )}
      {!collapsed && item.badge && (
        <span className="ml-auto rounded-md bg-brand-600/[0.15] px-1.5 py-0.5 text-xs font-medium text-brand-400">
          {item.badge}
        </span>
      )}
      {/* Tooltip when collapsed */}
      {collapsed && (
        <span className="pointer-events-none absolute left-full z-50 ml-2 whitespace-nowrap rounded-md border border-white/[0.08] bg-surface-100 px-2.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
          {item.label}
          {item.badge && (
            <span className="ml-1.5 text-brand-400">{item.badge}</span>
          )}
        </span>
      )}
    </Link>
  );
}

// ---------------------------------------------------------------------------
// User section (avatar + name + logout)
// ---------------------------------------------------------------------------

function UserSection({ collapsed }: { collapsed: boolean }) {
  const { user, logout } = useAuth();

  if (!user) return null;

  const initials = (user.full_name ?? user.username)
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className={cn(
        "border-t border-white/5 p-3",
        collapsed ? "flex justify-center" : "flex items-center gap-3"
      )}
    >
      {/* Avatar */}
      <div className="relative flex-shrink-0">
        {user.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.avatar_url}
            alt={user.full_name ?? user.username}
            className="h-8 w-8 rounded-full object-cover ring-2 ring-white/10"
          />
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600/20 text-xs font-semibold text-brand-300 ring-2 ring-white/10">
            {initials}
          </div>
        )}
        {/* Online indicator */}
        <span className="absolute bottom-0 right-0 block h-2 w-2 rounded-full bg-emerald-500 ring-1 ring-surface-50" />
      </div>

      {!collapsed && (
        <>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-white">
              {user.full_name ?? user.username}
            </p>
            <p className="truncate text-xs text-white/30">{user.role}</p>
          </div>
          <button
            onClick={() => void logout()}
            aria-label="Sign out"
            title="Sign out"
            className="flex-shrink-0 rounded-md p-1.5 text-white/30 transition-colors hover:bg-white/5 hover:text-white"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Logo mark
// ---------------------------------------------------------------------------

function LogoMark({ collapsed }: { collapsed: boolean }) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 border-b border-white/5 px-4 py-4",
        collapsed && "justify-center px-0"
      )}
    >
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-600 shadow-glow-sm">
        <Sparkles className="h-4 w-4 text-white" />
      </div>
      {!collapsed && (
        <div className="min-w-0">
          <p className="truncate text-sm font-bold text-white">Prabhu AI</p>
          <p className="text-xs text-white/30">Studio v1.0</p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Desktop sidebar
// ---------------------------------------------------------------------------

function DesktopSidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        "relative hidden h-full flex-col border-r border-white/5 bg-surface-50 transition-all duration-300 ease-in-out md:flex",
        sidebarCollapsed ? "w-[68px]" : "w-[256px]"
      )}
    >
      <LogoMark collapsed={sidebarCollapsed} />

      {/* Navigation */}
      <nav
        className={cn(
          "flex-1 space-y-0.5 overflow-y-auto overflow-x-hidden py-3 scrollbar-hidden",
          sidebarCollapsed ? "px-2" : "px-3"
        )}
        aria-label="Main navigation"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.href} item={item} collapsed={sidebarCollapsed} />
        ))}
      </nav>

      {/* Collapse toggle button */}
      <button
        onClick={toggleSidebar}
        aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        className={cn(
          "absolute -right-3 top-20 z-10 flex h-6 w-6 items-center justify-center",
          "rounded-full border border-white/10 bg-surface-100 text-white/40",
          "shadow-surface transition-all duration-150",
          "hover:border-white/20 hover:text-white",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        )}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="h-3 w-3" />
        ) : (
          <ChevronLeft className="h-3 w-3" />
        )}
      </button>

      {/* User section */}
      <UserSection collapsed={sidebarCollapsed} />
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Mobile drawer
// ---------------------------------------------------------------------------

function MobileDrawer() {
  const { mobileMenuOpen, closeMobileMenu } = useUIStore();

  return (
    <>
      {/* Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-white/5 bg-surface-50 transition-transform duration-300 ease-out md:hidden",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Mobile navigation"
        aria-hidden={!mobileMenuOpen}
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between border-b border-white/5 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-600">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">Prabhu AI</p>
              <p className="text-xs text-white/30">Studio v1.0</p>
            </div>
          </div>
          <button
            onClick={closeMobileMenu}
            aria-label="Close menu"
            className="btn-icon"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              collapsed={false}
              onClick={closeMobileMenu}
            />
          ))}
        </nav>

        <UserSection collapsed={false} />
      </aside>
    </>
  );
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export function Sidebar() {
  return (
    <>
      <DesktopSidebar />
      <MobileDrawer />
    </>
  );
}
