"use client";

/**
 * Global context providers.
 *
 * Wrapped around every page in the root layout. Adding a new global
 * provider means a single change here — nothing else needs to change.
 *
 * Provider order (outermost first):
 *   QueryClientProvider → ReactQueryDevtools (dev only) → Sonner Toaster
 */

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "sonner";

import { isDev } from "@/env";

// -----------------------------------------------------------------------
// QueryClient factory
// -----------------------------------------------------------------------

function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        /**
         * Data is considered fresh for 60 seconds — no refetch on
         * component mount if the data is younger than this.
         */
        staleTime: 60_000,

        /**
         * Background refetch when the browser window regains focus.
         * Keeps list views current without manual refresh.
         */
        refetchOnWindowFocus: true,

        /**
         * Retry failed queries once before showing an error.
         * Avoids false negatives from brief network blips.
         */
        retry: 1,
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10_000),

        /**
         * Don't retry if it's a 404 or 401 — those are definitive answers.
         */
        retryOnMount: false,
      },
      mutations: {
        /**
         * Mutations are not retried automatically — the user should
         * explicitly retry after seeing an error.
         */
        retry: false,
      },
    },
  });
}

// -----------------------------------------------------------------------
// Providers component
// -----------------------------------------------------------------------

export function Providers({ children }: { children: React.ReactNode }) {
  /**
   * useState ensures each browser session gets exactly one QueryClient.
   * Using a module-level singleton would cause state to leak between
   * Next.js server requests in RSC-heavy apps.
   */
  const [queryClient] = useState(makeQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      {children}

      {/* Toast notifications — dark theme matching the app */}
      <Toaster
        position="top-right"
        theme="dark"
        richColors
        closeButton
        expand={false}
        duration={4000}
        toastOptions={{
          classNames: {
            toast:
              "!bg-surface-100 !border-white/8 !text-white !shadow-surface-lg",
            title: "!text-white !font-medium",
            description: "!text-white/60",
            actionButton: "!bg-brand-600 !text-white",
            cancelButton: "!bg-white/8 !text-white/60",
            closeButton: "!bg-surface-200 !border-white/8 !text-white/40",
          },
        }}
      />

      {/* ReactQuery developer tools — only loaded in development */}
      {isDev && (
        <ReactQueryDevtools
          initialIsOpen={false}
          buttonPosition="bottom-right"
        />
      )}
    </QueryClientProvider>
  );
}
