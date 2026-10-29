import type { Metadata } from "next";
import "./globals.css";

import { AppHeader } from "@/components/app-header";
import { AnalysisProvider } from "@/contexts/analysis-context";

export const metadata: Metadata = {
  title: "Smart Gallery",
  description:
    "ต้นแบบผู้ช่วยจัดระเบียบคลังรูป วิเคราะห์คุณภาพและแนะนำรูปที่ดีที่สุด",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <body>
        <AnalysisProvider>
          <AppHeader />

          <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-7xl px-4 py-6">
            {children}
          </main>
        </AnalysisProvider>
      </body>
    </html>
  );
}
