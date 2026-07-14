"use client";

/**
 * Protected dashboard layout.
 *
 * Renders Sidebar + TopBar shell for all /(dashboard)/* routes.
 * Redirects unauthenticated users to /login.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, selectIsAuthenticated } from "@/store/auth-store";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { PageSpinner } from "@/components/ui/spinner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const isAuthenticated = useAuthStore(selectIsAuthenticated);

  // Client-side auth guard. A proper middleware check is in next.config.ts
  // for faster redirects without full JS execution.
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  // While Zustand store is hydrating from localStorage, show a spinner
  // to avoid a flash of unauthenticated content.
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <PageSpinner label="Checking authentication…" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main
          id="main-content"
          className="flex-1 overflow-y-auto p-6"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
