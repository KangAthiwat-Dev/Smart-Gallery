import { Lightbulb } from "lucide-react";

import { exposureLabels } from "@/lib/locale-th";
import type { AnalysisParameters, PhotoAnalysis } from "@/types/analysis";

type Props = {
  photo: PhotoAnalysis;
  thresholds: AnalysisParameters["exposure"];
};

function clamp(value: number) {
  return Math.max(0, Math.min(1, value));
}

function exposureDisplay({ photo, thresholds }: Props) {
  const metrics = photo.exposureMetrics;
  if (!metrics) {
    return {
      position: { underexposed: 15, normal: 46, overexposed: 80 }[
        photo.exposureLabel
      ],
      description: "วิเคราะห์รูปอีกครั้งเพื่อดูตำแหน่งระดับแสงโดยละเอียด",
    };
  }

  const { brightnessMean, darkClippingRatio, highlightClippingRatio } = metrics;
  if (photo.exposureLabel === "underexposed") {
    const severity = Math.max(
      clamp(
        (thresholds.low_brightness - brightnessMean) /
          Math.max(thresholds.low_brightness, 1),
      ),
      clamp(
        (darkClippingRatio - thresholds.dark_clip_threshold) /
          Math.max(1 - thresholds.dark_clip_threshold, 1e-9),
      ),
    );
    return {
      position: 4 + (1 - severity) * 22,
      description:
        darkClippingRatio >= thresholds.dark_clip_threshold
          ? "มีบริเวณที่มืดจัด รายละเอียดอาจหาย"
          : "ภาพโดยรวมค่อนข้างมืด",
    };
  }
  if (photo.exposureLabel === "overexposed") {
    const severity = Math.max(
      clamp(
        (brightnessMean - thresholds.high_brightness) /
          Math.max(255 - thresholds.high_brightness, 1),
      ),
      clamp(
        (highlightClippingRatio - thresholds.highlight_clip_threshold) /
          Math.max(1 - thresholds.highlight_clip_threshold, 1e-9),
      ),
    );
    return {
      position: 66 + severity * 30,
      description:
        highlightClippingRatio >= thresholds.highlight_clip_threshold
          ? "มีบริเวณที่สว่างจัด รายละเอียดอาจหาย"
          : "ภาพโดยรวมค่อนข้างสว่าง",
    };
  }
  return {
    position:
      34 +
      clamp(
        (brightnessMean - thresholds.low_brightness) /
          Math.max(thresholds.high_brightness - thresholds.low_brightness, 1),
      ) *
        24,
    description: "แสงอยู่ในระดับปกติ",
  };
}

export function ExposureGauge(props: Props) {
  const { position, description } = exposureDisplay(props);
  const label = exposureLabels[props.photo.exposureLabel];
  return (
    <div className="space-y-3" data-exposure-state={props.photo.exposureLabel}>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="flex items-center gap-2">
          <Lightbulb className="size-4" aria-hidden="true" />
          แสง
        </span>
        <span className="font-semibold">{label}</span>
      </div>
      <div role="img" aria-label={`ระดับแสง: ${label}`} className="pt-3">
        <div
          aria-hidden="true"
          className="relative h-2.5 rounded-full"
          style={{
            background:
              "linear-gradient(to right, #94a3b8 0%, #94a3b8 28%, #22c55e 34%, #22c55e 60%, #fb923c 68%, #f97316 80%, #ef4444 100%)",
          }}
        >
          <span
            data-exposure-marker
            className="absolute -top-2.5 h-0 w-0 -translate-x-1/2 border-x-[5px] border-t-[7px] border-x-transparent border-t-foreground"
            style={{ left: `${position}%` }}
          />
        </div>
        <div
          aria-hidden="true"
          className="mt-2 flex justify-between text-xs text-muted-foreground"
        >
          <span>มืด</span>
          <span>ปกติ</span>
          <span>สว่างเกิน</span>
        </div>
      </div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
