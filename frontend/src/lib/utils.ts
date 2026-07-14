/**
 * Shared utility functions used across the application.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { ApiError } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// Class name helpers
// ---------------------------------------------------------------------------

/** Merge Tailwind classes safely, resolving conflicts correctly. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// ---------------------------------------------------------------------------
// Date and time
// ---------------------------------------------------------------------------

const DATE_FORMATTER = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const DATETIME_FORMATTER = new Intl.DateTimeFormat("en-US", {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

/** Format a date string or Date object as "Jan 1, 2025". */
export function formatDate(value: string | Date): string {
  return DATE_FORMATTER.format(new Date(value));
}

/** Format a date string or Date object as "Jan 1, 2025, 12:00 PM". */
export function formatDateTime(value: string | Date): string {
  return DATETIME_FORMATTER.format(new Date(value));
}

/**
 * Return a human-readable relative time string.
 * Examples: "just now", "3 minutes ago", "2 days ago"
 */
export function timeAgo(value: string | Date): string {
  const seconds = Math.floor(
    (Date.now() - new Date(value).getTime()) / 1000
  );

  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds} seconds ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
  return formatDate(value);
}

/** Format a duration in seconds as "1h 23m 45s". */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const parts: string[] = [];
  if (h > 0) parts.push(`${h}h`);
  if (m > 0) parts.push(`${m}m`);
  parts.push(`${s}s`);
  return parts.join(" ");
}

// ---------------------------------------------------------------------------
// File size
// ---------------------------------------------------------------------------

/** Format a byte count as "1.5 MB", "345 KB", etc. */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

// ---------------------------------------------------------------------------
// String helpers
// ---------------------------------------------------------------------------

/** Truncate a string to the given length, adding "…" if truncated. */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trimEnd()}…`;
}

/** Capitalize the first letter of a string. */
export function capitalize(text: string): string {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

/** Convert snake_case or kebab-case to Title Case. */
export function toTitleCase(text: string): string {
  return text
    .replace(/[-_]/g, " ")
    .replace(/\w\S*/g, (word) => capitalize(word));
}

/** Get initials from a full name. "John Doe" → "JD". */
export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// ---------------------------------------------------------------------------
// Error helpers
// ---------------------------------------------------------------------------

/** Extract a user-readable message from any thrown value. */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  return "An unexpected error occurred.";
}

/** Type guard: check if an error is an ApiError. */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof Error && error.name === "ApiError";
}

// ---------------------------------------------------------------------------
// Number formatting
// ---------------------------------------------------------------------------

/** Format a number with thousands separators: 1234567 → "1,234,567". */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

/** Clamp a number between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

// ---------------------------------------------------------------------------
// Async helpers
// ---------------------------------------------------------------------------

/** Promise that resolves after the given number of milliseconds. */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
