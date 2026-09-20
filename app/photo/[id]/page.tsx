import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Aperture, ArrowLeft, Lightbulb, Star } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { photos } from "@/data/mock-data";

type Props = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return photos.map((photo) => ({ id: photo.id }));
}

export default async function PhotoDetailPage({ params }: Props) {
  const { id } = await params;
  const photo = photos.find((item) => item.id === id);

  if (!photo) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Link
        href="/gallery"
        className={buttonVariants({ variant: "ghost" })}
      >
        <ArrowLeft />
        Back to Gallery
      </Link>

      <div className="grid gap-6 md:grid-cols-[1.2fr_1fr]">
        <div className="relative aspect-4/5 overflow-hidden rounded-xl bg-muted">
          <Image
            src={photo.imageUrl}
            alt={photo.filename}
            fill
            priority
            sizes="(min-width: 768px) 55vw, 100vw"
            className="object-cover"
          />
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground">{photo.filename}</p>

            <div className="mt-2 flex flex-wrap items-center gap-2">
              <StatusBadge status={photo.recommendation} />

              {photo.bestShot && (
                <span className="flex items-center gap-1 text-sm font-medium">
                  <Star className="size-4 fill-current" />
                  Best Shot
                </span>
              )}
            </div>
          </div>

          <Card>
            <CardContent className="space-y-6 pt-6">
              <Score label="Quality" value={photo.qualityScore} />

              <Separator />

              <Score
                label="Sharpness"
                value={photo.sharpnessScore}
                icon={<Aperture className="size-4" />}
              />

              <Score
                label="Exposure"
                value={photo.exposureScore}
                icon={<Lightbulb className="size-4" />}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3 pt-6">
              <h2 className="font-semibold">Why this recommendation?</h2>

              <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {photo.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            File size: {photo.fileSizeMB.toFixed(1)} MB
          </p>
        </div>
      </div>
    </div>
  );
}

function Score({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon?: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-sm">
          {icon}
          {label}
        </span>

        <span className="font-semibold">{value}/100</span>
      </div>

      <Progress
        value={value}
        aria-label={`${label} score`}
        aria-valuetext={`${value} out of 100`}
      />
    </div>
  );
}
