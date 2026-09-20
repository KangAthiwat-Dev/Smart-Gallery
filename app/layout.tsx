import type { Metadata } from "next";
import "./globals.css";

import { AppHeader } from "@/components/app-header";

export const metadata: Metadata = {
  title: "Smart Gallery",
  description:
    "Intelligent photo cleanup and best-shot recommendation prototype",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppHeader />

        <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-7xl px-4 py-6">
          {children}
        </main>
      </body>
    </html>
  );
}