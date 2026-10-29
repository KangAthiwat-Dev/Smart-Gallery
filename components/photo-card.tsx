import Image from "next/image";
import Link from "next/link";
import { Star } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import type { PhotoAnalysis } from "@/types/analysis";
import { formatBytes } from "@/lib/locale-th";

type Props = {
  photo: PhotoAnalysis;
  returnTo?: string;
};

export function PhotoCard({ photo, returnTo = "/gallery" }: Props) {
  const anchor = `photo-${photo.id}`;
  const query = new URLSearchParams({ from: `${returnTo}#${anchor}` });
  return (
    <Link
      id={anchor}
      href={`/photo/${encodeURIComponent(photo.id)}?${query}`}
      className="block scroll-mt-24 rounded-xl outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <Card className="group relative overflow-hidden border-0 p-0 shadow-sm">
        <div className="relative aspect-4/5 overflow-hidden bg-muted">
          <Image
            src={photo.imageUrl}
            alt={photo.filename}
            fill
            unoptimized
            sizes="(min-width: 1280px) 20vw, (min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw"
            className="object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />

          {photo.bestShot && (
            <div className="absolute left-2 top-2 flex max-w-[calc(100%-1rem)] items-center gap-1 rounded-xl bg-black/70 px-2 py-1 text-[11px] text-white sm:text-xs">
              <Star className="size-3 shrink-0 fill-current" />
              {photo.bestShotNeedsReview || photo.recommendation === "REVIEW"
                ? "รูปที่ดีที่สุด · รอตรวจสอบ"
                : "รูปที่ดีที่สุด"}
            </div>
          )}

          <div className="absolute bottom-2 left-2">
            <StatusBadge status={photo.recommendation} />
          </div>
        </div>

        <div className="space-y-1 p-3">
          <p className="truncate text-sm font-medium">{photo.filename}</p>

          <div className="flex flex-wrap justify-between gap-x-2 gap-y-1 text-xs text-muted-foreground">
            <span>คุณภาพ {photo.qualityScore}</span>
            <span>{formatBytes(photo.fileSizeBytes)}</span>
          </div>
        </div>
      </Card>
    </Link>
  );
}
