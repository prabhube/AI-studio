import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { Providers } from "./providers";
import "@/styles/globals.css";

// -----------------------------------------------------------------------
// Fonts — loaded via next/font (no external CDN request at runtime,
// fonts are self-hosted by Next.js automatically).
// -----------------------------------------------------------------------

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
  // Subset to weights we actually use — reduces bundle size
  weight: ["400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
  weight: ["400", "500"],
});

// -----------------------------------------------------------------------
// App-wide metadata (overridable per-page via generateMetadata or
// individual page exports)
// -----------------------------------------------------------------------

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"
  ),
  title: {
    default: "Prabhu AI Studio",
    template: "%s | Prabhu AI Studio",
  },
  description:
    "Local-first AI video generation studio. Create complete videos from text prompts using open-source models — all running on your own machine.",
  keywords: [
    "AI video generation",
    "stable diffusion",
    "local AI",
    "text to video",
    "Piper TTS",
    "Whisper",
    "FFmpeg",
    "open source AI",
  ],
  authors: [{ name: "Prabhu AI Studio" }],
  robots: {
    index: false, // private tool — don't index in search engines
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#6366f1",
  width: "device-width",
  initialScale: 1,
  // Prevent zoom on form focus on iOS
  maximumScale: 1,
};

// -----------------------------------------------------------------------
// Root layout — wraps every page in the application.
// The `dark` class on <html> enables Tailwind's dark mode variant globally.
// -----------------------------------------------------------------------

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen bg-surface font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
