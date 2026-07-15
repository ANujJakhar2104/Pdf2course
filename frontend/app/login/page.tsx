"use client";

import { createClient } from "@/lib/supabaseClient";

export default function LoginPage() {
  const supabase = createClient();

  const handleGoogleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  };

  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm rounded-xl border p-8 text-center">
        <h1 className="mb-6 text-2xl font-semibold">PDF → E-Course</h1>
        <button
          onClick={handleGoogleLogin}
          className="w-full rounded-lg bg-black py-2.5 text-white hover:bg-neutral-800"
        >
          Continue with Google
        </button>
      </div>
    </main>
  );
}
