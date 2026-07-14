"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff, Check, X } from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Password strength
// ---------------------------------------------------------------------------

interface StrengthRule {
  label: string;
  test: (v: string) => boolean;
}

const STRENGTH_RULES: StrengthRule[] = [
  { label: "At least 8 characters", test: (v) => v.length >= 8 },
  { label: "Uppercase letter (A-Z)", test: (v) => /[A-Z]/.test(v) },
  { label: "Lowercase letter (a-z)", test: (v) => /[a-z]/.test(v) },
  { label: "Digit (0-9)", test: (v) => /\d/.test(v) },
  {
    label: "Special character (!@#$…)",
    test: (v) => /[!@#$%^&*()_+\-=[\]{}|;':",./<>?]/.test(v),
  },
];

function StrengthMeter({ password }: { password: string }) {
  if (!password) return null;
  const passed = STRENGTH_RULES.filter((r) => r.test(password)).length;
  const pct = (passed / STRENGTH_RULES.length) * 100;

  const barColor =
    passed <= 1
      ? "bg-red-500"
      : passed <= 3
        ? "bg-amber-500"
        : "bg-emerald-500";

  const label =
    passed <= 1 ? "Weak" : passed <= 3 ? "Fair" : passed === 5 ? "Strong" : "Good";

  return (
    <div className="mt-2 space-y-2">
      {/* Progress bar */}
      <div className="flex items-center gap-2">
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/8">
          <div
            className={cn("h-full rounded-full transition-all duration-300", barColor)}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="min-w-[3rem] text-right text-xs text-white/40">{label}</span>
      </div>

      {/* Rule list */}
      <ul className="space-y-1">
        {STRENGTH_RULES.map((rule) => {
          const ok = rule.test(password);
          return (
            <li key={rule.label} className="flex items-center gap-2 text-xs">
              {ok ? (
                <Check className="h-3 w-3 flex-shrink-0 text-emerald-400" />
              ) : (
                <X className="h-3 w-3 flex-shrink-0 text-white/20" />
              )}
              <span className={ok ? "text-white/60" : "text-white/30"}>
                {rule.label}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Validation schema
// ---------------------------------------------------------------------------

const registerSchema = z
  .object({
    email: z.string().email("Enter a valid email address."),
    username: z
      .string()
      .min(3, "Username must be at least 3 characters.")
      .max(50, "Username must be at most 50 characters.")
      .regex(/^[a-zA-Z0-9_-]+$/, "Only letters, numbers, underscores, and hyphens."),
    full_name: z.string().max(255).optional(),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .max(128)
      .refine((v) => /[A-Z]/.test(v), "Needs an uppercase letter.")
      .refine((v) => /[a-z]/.test(v), "Needs a lowercase letter.")
      .refine((v) => /\d/.test(v), "Needs a digit.")
      .refine(
        (v) => /[!@#$%^&*()_+\-=[\]{}|;':",./<>?]/.test(v),
        "Needs a special character."
      ),
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

// ---------------------------------------------------------------------------
// Register page
// ---------------------------------------------------------------------------

export default function RegisterPage() {
  const { register: registerUser, loginWithGoogle, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const passwordValue = watch("password") ?? "";

  const onSubmit = async (values: RegisterFormValues) => {
    setServerError(null);
    try {
      await registerUser({
        email: values.email,
        username: values.username,
        password: values.password,
        full_name: values.full_name || undefined,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message);
      } else {
        setServerError("Something went wrong. Please try again.");
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
        <h1 className="text-2xl font-bold text-white">Create account</h1>
        <p className="mt-1 text-sm text-white/45">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-400 hover:text-brand-300 transition-colors">
            Sign in
          </Link>
        </p>
      </div>

      {/* Google sign-up */}
      <button
        type="button"
        onClick={handleGoogleLogin}
        disabled={googleLoading}
        className={cn(
          "btn-secondary w-full gap-3",
          googleLoading && "cursor-not-allowed opacity-50"
        )}
      >
        <svg className="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
        Continue with Google
      </button>

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 border-t border-white/8" />
        <span className="text-xs text-white/25">or register with email</span>
        <div className="flex-1 border-t border-white/8" />
      </div>

      {/* Form */}
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
          label="Username"
          type="text"
          autoComplete="username"
          placeholder="yourname"
          hint="Letters, numbers, underscores, hyphens."
          error={errors.username?.message}
          {...register("username")}
        />

        <Input
          label="Full name"
          type="text"
          autoComplete="name"
          placeholder="Optional"
          error={errors.full_name?.message}
          {...register("full_name")}
        />

        <div>
          <Input
            label="Password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            placeholder="••••••••"
            error={errors.password?.message}
            rightElement={
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="text-white/30 hover:text-white/60 transition-colors"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
            {...register("password")}
          />
          <StrengthMeter password={passwordValue} />
        </div>

        <Input
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••"
          error={errors.confirm_password?.message}
          {...register("confirm_password")}
        />

        {/* Server error */}
        {serverError && (
          <div
            className="rounded-lg border border-red-500/20 bg-red-500/8 px-4 py-3 text-sm text-red-400"
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
          Create account
        </Button>
      </form>

      <p className="text-center text-xs text-white/25">
        By creating an account you agree to our{" "}
        <span className="text-white/40">Terms of Service</span>.
      </p>
    </div>
  );
}
