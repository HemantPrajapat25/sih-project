import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { AppLayoutClient } from "./layout-client";

export const metadata: Metadata = {
  title: "NumberGuard | Telecom Mobile Number Lifecycle & Risk Management",
  description:
    "Privacy-preserving B2B platform helping telecom operators manage decommissioned mobile numbers before reallocation to new subscribers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
        <AuthProvider>
          <AppLayoutClient>{children}</AppLayoutClient>
        </AuthProvider>
      </body>
    </html>
  );
}
