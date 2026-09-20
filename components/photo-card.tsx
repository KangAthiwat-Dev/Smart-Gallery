import Image from "next/image";
import Link from "next/link";
import { Star } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import type { PhotoAnalysis } from "@/types/analysis";

type Props = {
  photo: PhotoAnalysis;
};

export function PhotoCard({ photo }: Props) {
  return (
    <Link
      href={`/photo/${photo.id}`}
      className="block rounded-xl outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <Card className="group relative overflow-hidden border-0 p-0 shadow-sm">
        <div className="relative aspect-4/5 overflow-hidden bg-muted">
          <Image
            src={photo.imageUrl}
            alt=""
            fill
            sizes="(min-width: 1280px) 20vw, (min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw"
            className="object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />

          {photo.bestShot && (
            <div className="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-black/70 px-2 py-1 text-xs text-white">
              <Star className="size-3 fill-current" />
              Best Shot
            </div>
          )}

          <div className="absolute bottom-2 left-2">
            <StatusBadge status={photo.recommendation} />
          </div>
        </div>

        <div className="space-y-1 p-3">
          <p className="truncate text-sm font-medium">{photo.filename}</p>

          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Quality {photo.qualityScore}</span>
            <span>{photo.fileSizeMB.toFixed(1)} MB</span>
          </div>
        </div>
      </Card>
    </Link>
  );
}
