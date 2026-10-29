"use client";

import {
  HardDrive,
  Images,
  ShieldCheck,
  TriangleAlert,
  Trash2,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { AnalysisEmpty } from "@/components/analysis-empty";
import { AnalysisNotices } from "@/components/analysis-notices";
import { useAnalysis } from "@/contexts/analysis-context";
import {
  formatBytes,
  formatThaiDate,
  sharpnessMethodLabels,
} from "@/lib/locale-th";

export default function SummaryPage() {
  const { analysis, isRestoring } = useAnalysis();
  if (isRestoring || !analysis)
    return <AnalysisEmpty isRestoring={isRestoring} />;
  const { photos, summary, parameters } = analysis;
  const timedPhashThreshold =
    parameters.similarity.strategy === "exif_time_or_phash"
      ? parameters.similarity.timed_phash_threshold
      : null;
  const keep = photos.filter((photo) => photo.recommendation === "KEEP");

  const review = photos.filter((photo) => photo.recommendation === "REVIEW");

  const deleteCandidates = photos.filter(
    (photo) => photo.recommendation === "RECOMMEND_DELETE",
  );

  const estimatedSaving = summary.estimatedStorageSavingMB;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">
          สรุปผลวิเคราะห์
        </h1>

        <p className="text-sm text-muted-foreground">
          ภาพรวมผลวิเคราะห์ของรูปชุดปัจจุบัน
        </p>
      </header>

      <AnalysisNotices />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="วิเคราะห์แล้ว"
          value={photos.length}
          icon={<Images />}
        />

        <SummaryCard
          title="แนะนำให้เก็บ"
          value={keep.length}
          icon={<ShieldCheck />}
        />

        <SummaryCard
          title="ควรตรวจสอบ"
          value={review.length}
          icon={<TriangleAlert />}
        />

        <SummaryCard
          title="แนะนำให้ลบ"
          value={deleteCandidates.length}
          icon={<Trash2 />}
        />
      </div>

      <Card>
        <CardContent className="flex items-center gap-4 pt-6">
          <div className="flex size-12 items-center justify-center rounded-xl bg-muted">
            <HardDrive className="size-5" />
          </div>

          <div>
            <p className="text-sm text-muted-foreground">
              พื้นที่ที่อาจประหยัดได้
            </p>

            <p className="text-3xl font-semibold">
              {formatBytes(estimatedSaving * 1024 * 1024)}
            </p>
          </div>
        </CardContent>
      </Card>

      <p className="text-sm text-muted-foreground">
        ระบบให้คำแนะนำเท่านั้น ไม่มีการลบรูปให้อัตโนมัติ
      </p>
      <Card>
        <CardContent className="space-y-3 pt-6">
          <h2 className="font-semibold">ค่าที่ใช้วิเคราะห์</h2>
          <p className="text-sm text-muted-foreground">
            วิเคราะห์เสร็จเมื่อ {formatThaiDate(analysis.completedAt)}
            {" · "}คะแนนคุณภาพใช้ความคมชัด{" "}
            {(parameters.quality_score.sharpness_weight * 100).toFixed(0)}%
            {" และแสง "}
            {(parameters.quality_score.exposure_weight * 100).toFixed(0)}%
            คะแนนนี้อธิบายคุณสมบัติของรูป ไม่ใช่ความแม่นยำในการทำนาย
          </p>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">
                Sharpness method / Threshold
              </dt>
              <dd>
                {sharpnessMethodLabels[parameters.sharpness.method] ||
                  parameters.sharpness.method}{" "}
                / {parameters.sharpness.threshold.toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Brightness range</dt>
              <dd>
                {parameters.exposure.low_brightness}–
                {parameters.exposure.high_brightness}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Similarity strategy</dt>
              <dd>
                {parameters.similarity.strategy === "exif_time_or_phash"
                  ? timedPhashThreshold != null
                    ? "EXIF time → Timed pHash fallback"
                    : "EXIF time only"
                  : "EXIF + pHash"}
                {" · "}
                {parameters.similarity.linkage === "average"
                  ? "Average-link"
                  : "Complete-link"}
                {parameters.similarity.strategy === "exif_time_or_phash" &&
                  " (untimed photos)"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">
                Missing timestamp policy
              </dt>
              <dd>
                {parameters.similarity.missing_exif_policy === "phash"
                  ? "pHash only · separate pool"
                  : "Strict · exclude untimed photos"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">
                {parameters.similarity.strategy === "exif_time_or_phash"
                  ? "Untimed pHash threshold / EXIF window"
                  : "pHash threshold / EXIF window"}
              </dt>
              <dd>
                ≤ {parameters.similarity.phash_threshold} /{" "}
                {parameters.similarity.exif_time_window_seconds === null
                  ? "ไม่จำกัด"
                  : `${parameters.similarity.exif_time_window_seconds} วินาที`}
              </dd>
            </div>
            {parameters.similarity.strategy === "exif_time_or_phash" && (
              <div>
                <dt className="text-muted-foreground">Timed pHash threshold</dt>
                <dd>
                  {timedPhashThreshold != null
                    ? `≤ ${timedPhashThreshold} · outside EXIF window`
                    : "Disabled · time only"}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-muted-foreground">Best Shot tie margin</dt>
              <dd>
                ต่างกันน้อยกว่า {parameters.recommendation.best_shot_tie_margin}{" "}
                คะแนน: รูปที่คะแนนใกล้กันต้องตรวจสอบ
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Group refinement</dt>
              <dd>
                {parameters.similarity.strategy === "exif_time_or_phash"
                  ? timedPhashThreshold != null
                    ? "Time groups → Complete-link timed pHash merge"
                    : "Direct time / pHash grouping"
                  : "Singleton Rescue + Group Merge + Safety Guards"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Duplicate quality gap</dt>
              <dd>
                ต่ำกว่ารูปที่ดีที่สุดอย่างน้อย{" "}
                {parameters.recommendation.duplicate_quality_gap} คะแนน
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between pt-6">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>

          <p className="text-3xl font-semibold">{value}</p>
        </div>

        <div className="text-muted-foreground [&>svg]:size-5">{icon}</div>
      </CardContent>
    </Card>
  );
}
