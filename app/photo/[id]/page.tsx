"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Aperture, ArrowLeft, Star } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { AnalysisEmpty } from "@/components/analysis-empty";
import { ExposureGauge } from "@/components/exposure-gauge";
import { useAnalysis } from "@/contexts/analysis-context";
import {
  exposureLabels,
  sharpnessLabels,
  formatBytes,
  formatThaiDate,
  translateAnalysisText,
} from "@/lib/locale-th";
import { photoReturnHref } from "@/lib/navigation";

export default function PhotoDetailPage() {
  return (
    <Suspense fallback={<AnalysisEmpty isRestoring />}>
      <PhotoDetailContent />
    </Suspense>
  );
}

function PhotoDetailContent() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const returnTo = photoReturnHref(searchParams.get("from"));
  const backLabel = returnTo.startsWith("/groups")
    ? "กลับไปกลุ่มรูปคล้าย"
    : "กลับไปคลังรูป";
  const { analysis, isRestoring } = useAnalysis();
  if (isRestoring || !analysis)
    return <AnalysisEmpty isRestoring={isRestoring} />;
  const photo = analysis.photos.find((item) => item.id === id);

  if (!photo) {
    return (
      <div className="space-y-4 py-16 text-center">
        <h1 className="text-2xl font-semibold">ไม่พบรูปนี้ในผลวิเคราะห์</h1>
        <p className="text-sm text-muted-foreground">
          ผลวิเคราะห์อาจถูกแทนที่ด้วยรูปชุดใหม่แล้ว
        </p>
        <Link
          href={returnTo}
          aria-label={backLabel}
          title={backLabel}
          className={buttonVariants({
            variant: "outline",
            size: "icon",
            className: "size-11 rounded-full",
          })}
        >
          <ArrowLeft aria-hidden="true" />
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Link
        href={returnTo}
        aria-label={backLabel}
        title={backLabel}
        className={buttonVariants({
          variant: "ghost",
          size: "icon",
          className: "size-11 rounded-full",
        })}
      >
        <ArrowLeft aria-hidden="true" />
      </Link>

      <div className="grid gap-6 md:grid-cols-[1.2fr_1fr]">
        <div className="relative aspect-4/5 overflow-hidden rounded-xl bg-muted">
          <Image
            src={photo.imageUrl}
            alt={photo.filename}
            fill
            unoptimized
            priority
            sizes="(min-width: 768px) 55vw, 100vw"
            className="object-cover"
          />
        </div>

        <div className="space-y-4">
          <div>
            <h1 className="wrap-break-word text-lg font-semibold">
              {photo.filename}
            </h1>
            <p className="break-all text-xs text-muted-foreground">
              {photo.relativePath}
            </p>

            <div className="mt-2 flex flex-wrap items-center gap-2">
              <StatusBadge status={photo.recommendation} />

              {photo.bestShot && (
                <span className="flex items-center gap-1 text-sm font-medium">
                  <Star className="size-4 fill-current" />
                  {photo.bestShotNeedsReview ||
                  photo.recommendation === "REVIEW"
                    ? "รูปที่ดีที่สุดเบื้องต้น · รอตรวจสอบ"
                    : "รูปที่ดีที่สุด"}
                </span>
              )}
            </div>
          </div>

          <Card>
            <CardContent className="space-y-6 pt-6">
              <Score label="คุณภาพ" value={photo.qualityScore} />

              <Separator />

              <Score
                label="ความคมชัด"
                value={photo.sharpnessScore}
                icon={<Aperture className="size-4" />}
              />

              <ExposureGauge
                photo={photo}
                thresholds={analysis.parameters.exposure}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3 pt-6">
              <h2 className="font-semibold">เหตุผลของคำแนะนำ</h2>

              <ul className="list-disc space-y-2 pl-5 text-sm text-muted-foreground">
                {photo.reasons.map((reason) => (
                  <li key={reason}>{translateAnalysisText(reason)}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            ขนาดไฟล์: {formatBytes(photo.fileSizeBytes)}
          </p>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">ความคมชัด</dt>
              <dd>{sharpnessLabels[photo.sharpnessLabel]}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">แสง</dt>
              <dd>{exposureLabels[photo.exposureLabel]}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">ขนาดภาพ</dt>
              <dd>
                {photo.width} × {photo.height} px
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">กลุ่มรูปคล้าย</dt>
              <dd>{photo.similarityGroup || "ไม่อยู่ในกลุ่ม"}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-muted-foreground">เวลาถ่าย</dt>
              <dd>
                {photo.takenAt
                  ? formatThaiDate(photo.takenAt)
                  : "ไม่มีข้อมูลเวลาถ่าย"}
              </dd>
            </div>
          </dl>
          <p className="text-xs text-muted-foreground">
            คะแนนคุณภาพและความคมชัดเต็ม 100 คะแนน
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

        <span className="font-semibold">{value.toFixed(1)}/100</span>
      </div>

      <Progress
        value={value}
        aria-label={`คะแนน${label}`}
        aria-valuetext={`${value} จาก 100 คะแนน`}
      />
    </div>
  );
}
