"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Zap } from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Demo login — bypasses the backend for local development/demo
// ---------------------------------------------------------------------------

function useDemoLogin() {
  const router = useRouter();
  const store = useAuthStore();

  return () => {
    // Inject a mock user and a fake (non-expiring) token so the auth guard passes
    store.setTokens({
      accessToken: "demo_access_token_local_only",
      refreshToken: "demo_refresh_token_local_only",
      expiresIn: 86400 * 365, // 1 year
      issuedAt: Date.now(),
    });
    store.setUser({
      id: "00000000-0000-0000-0000-000000000001",
      email: "demo@prabhuai.studio",
      username: "demo_user",
      full_name: "Demo User",
      avatar_url: null,
      role: "admin",
      is_active: true,
      is_superuser: true,
      email_verified: true,
      oauth_provider: null,
      last_login_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    router.push("/dashboard");
  };
}

// ---------------------------------------------------------------------------
// Validation schema
// ---------------------------------------------------------------------------

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// ---------------------------------------------------------------------------
// Google button
// ---------------------------------------------------------------------------

function GoogleSignInButton({ onClick, loading }: { onClick: () => void; loading: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className={cn(
        "btn-secondary w-full gap-3",
        loading && "cursor-not-allowed opacity-50"
      )}
    >
      {/* Google G logo */}
      <svg className="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          fill="#4285F4"
        />
        <path
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          fill="#34A853"
        />
        <path
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          fill="#FBBC05"
        />
        <path
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          fill="#EA4335"
        />
      </svg>
      Continue with Google
    </button>
  );
}

// ---------------------------------------------------------------------------
// Login page
// ---------------------------------------------------------------------------

export default function LoginPage() {
  const { login, loginWithGoogle, isLoading } = useAuth();
  const demoLogin = useDemoLogin();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const [isNetworkError, setIsNetworkError] = useState(false);

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    setIsNetworkError(false);
    try {
      await login(values);
    } catch (err) {
      if (err instanceof ApiError) {
        // Detect network/connection errors (backend not running)
        const msg = err.message ?? "";
        if (
          msg.toLowerCase().includes("network") ||
          msg.toLowerCase().includes("connection") ||
          msg.toLowerCase().includes("fetch") ||
          err.status === 0
        ) {
          setIsNetworkError(true);
          setServerError(null);
        } else {
          setServerError(msg);
        }
      } else if (err instanceof TypeError && (err as TypeError).message.includes("fetch")) {
        setIsNetworkError(true);
      } else {
        setIsNetworkError(true); // treat any unknown error as backend-down
      }
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      await loginWithGoogle();
    } finally {
      setGoogleLoading(false);
    }
  };

  const busy = isSubmitting || isLoading;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Heading */}
      <div>
        <h1 className="text-2xl font-bold text-white">Sign in</h1>
        <p className="mt-1 text-sm text-white/45">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-brand-400 hover:text-brand-300 transition-colors">
            Create one
          </Link>
        </p>
      </div>

      {/* ── Demo Login (no backend required) ── */}
      <div className="rounded-xl border border-brand-500/30 bg-brand-600/[0.08] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-brand-400" />
          <span className="text-sm font-semibold text-brand-300">Demo Mode</span>
          <span className="ml-auto rounded-full bg-brand-500/20 px-2 py-0.5 text-xs text-brand-400">
            No backend needed
          </span>
        </div>
        <p className="text-xs text-white/50">
          Skip login and explore the full 15-step AI pipeline UI instantly.
          Backend API calls will show errors until the server is running.
        </p>
        <button
          type="button"
          onClick={demoLogin}
          className="w-full rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold py-2.5 transition-colors flex items-center justify-center gap-2"
        >
          <Zap className="h-4 w-4" />
          Enter as Demo User
        </button>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 border-t border-white/[0.08]" />
        <span className="text-xs text-white/25">or sign in with account</span>
        <div className="flex-1 border-t border-white/[0.08]" />
      </div>

      {/* Google sign-in */}
      <GoogleSignInButton onClick={handleGoogleLogin} loading={googleLoading} />

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 border-t border-white/[0.08]" />
        <span className="text-xs text-white/25">or continue with email</span>
        <div className="flex-1 border-t border-white/[0.08]" />
      </div>

      {/* Email / password form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Input
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          error={errors.email?.message}
          {...register("email")}
        />

        <Input
          label="Password"
          type={showPassword ? "text" : "password"}
          autoComplete="current-password"
          placeholder="••••••••"
          error={errors.password?.message}
          rightElement={
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="text-white/30 hover:text-white/60 transition-colors"
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          }
          {...register("password")}
        />

        {/* Network error — backend not running */}
        {isNetworkError && (
          <div
            className="rounded-xl border border-amber-500/30 bg-amber-500/[0.08] p-4 space-y-3"
            role="alert"
          >
            <p className="text-sm font-semibold text-amber-300">
              ⚠️ Backend server is not running
            </p>
            <p className="text-xs text-amber-200/70">
              The API at <span className="font-mono">localhost:8000</span> is unreachable.
              Use Demo Login to explore the full UI without a server.
            </p>
            <button
              type="button"
              onClick={demoLogin}
              className="w-full rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold py-2.5 transition-colors flex items-center justify-center gap-2"
            >
              <Zap className="h-4 w-4" />
              Enter as Demo User — Skip Login
            </button>
          </div>
        )}

        {/* Server error (auth failure, not network) */}
        {serverError && !isNetworkError && (
          <div
            className="rounded-lg border border-red-500/20 bg-red-500/[0.08] px-4 py-3 text-sm text-red-400"
            role="alert"
          >
            {serverError}
          </div>
        )}

        <Button
          type="submit"
          variant="primary"
          size="md"
          loading={busy}
          className="w-full"
        >
          Sign in
        </Button>
      </form>

      {/* Backend credentials note */}
      <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-xs text-white/40 space-y-1">
        <p className="font-medium text-white/50">Backend credentials (when server is running):</p>
        <p>Email: <span className="text-white/70 font-mono">admin@prabhuai.studio</span></p>
        <p>Password: <span className="text-white/70 font-mono">Admin@123456</span></p>
        <p className="text-white/30 pt-1">Register a new account if the backend is connected.</p>
      </div>

      <p className="text-center text-xs text-white/25">
        By signing in you agree to our{" "}
        <span className="text-white/40">Terms of Service</span> and{" "}
        <span className="text-white/40">Privacy Policy</span>.
      </p>
    </div>
  );
}
