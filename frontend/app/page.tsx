"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function RootPage() {
  const router = useRouter();
  const { getDashboard, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      router.replace(getDashboard());
    }
  }, [isLoading, getDashboard, router]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
        <p className="text-sm text-slate-400">Routing to your portal…</p>
      </div>
    </div>
  );
}
