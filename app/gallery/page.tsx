"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { PhotoCard } from "@/components/photo-card";
import { buttonVariants } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AnalysisEmpty } from "@/components/analysis-empty";
import { AnalysisNotices } from "@/components/analysis-notices";
import { useAnalysis } from "@/contexts/analysis-context";
import { galleryHref, readGalleryFilter } from "@/lib/navigation";
import { formatBytes } from "@/lib/locale-th";

export default function GalleryPage() {
  return (
    <Suspense fallback={<AnalysisEmpty isRestoring />}>
      <GalleryContent />
    </Suspense>
  );
}

function GalleryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const filter = readGalleryFilter(searchParams.get("filter"));
  const { analysis, isRestoring } = useAnalysis();

  if (isRestoring || !analysis)
    return <AnalysisEmpty isRestoring={isRestoring} />;

  const { photos, summary } = analysis;

  const filteredPhotos =
    filter === "ALL"
      ? photos
      : photos.filter((photo) => photo.recommendation === filter);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">คลังรูป</h1>

        <p className="text-sm text-muted-foreground">
          วิเคราะห์แล้ว {summary.totalPhotos} รูป
        </p>
        <Link
          href="/"
          className={buttonVariants({ variant: "outline", className: "mt-3" })}
        >
          วิเคราะห์รูปชุดใหม่
        </Link>
      </header>

      <AnalysisNotices />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryItem label="แนะนำให้เก็บ" value={summary.keepCount} />

        <SummaryItem label="ควรตรวจสอบ" value={summary.reviewCount} />

        <SummaryItem label="แนะนำให้ลบ" value={summary.recommendDeleteCount} />

        <SummaryItem
          label="พื้นที่ที่อาจประหยัดได้"
          value={formatBytes(summary.estimatedStorageSavingMB * 1024 * 1024)}
        />
      </div>

      <Tabs
        value={filter}
        onValueChange={(value) =>
          router.replace(galleryHref(readGalleryFilter(String(value))), {
            scroll: false,
          })
        }
      >
        <TabsList aria-label="กรองตามคำแนะนำ" className="h-auto flex-wrap">
          <TabsTrigger value="ALL">ทั้งหมด</TabsTrigger>

          <TabsTrigger value="KEEP">เก็บ</TabsTrigger>

          <TabsTrigger value="REVIEW">ตรวจสอบ</TabsTrigger>

          <TabsTrigger value="RECOMMEND_DELETE">แนะนำให้ลบ</TabsTrigger>
        </TabsList>
        <TabsContent key={filter} value={filter}>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {filteredPhotos.map((photo) => (
              <PhotoCard
                key={photo.id}
                photo={photo}
                returnTo={galleryHref(filter)}
              />
            ))}
          </div>

          {filteredPhotos.length === 0 && (
            <div className="py-20 text-center text-sm text-muted-foreground">
              ไม่มีรูปในหมวดหมู่นี้
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function SummaryItem({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>

      <p className="mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
