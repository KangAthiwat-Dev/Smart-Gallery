"use client";

import { useAnalysis } from "@/contexts/analysis-context";
import { translateAnalysisText } from "@/lib/locale-th";

export function AnalysisNotices() {
  const { analysis, storageWarning } = useAnalysis();
  return (
    <div className="space-y-3 text-sm">
      {storageWarning && (
        <p role="status" className="rounded-xl border p-4">
          {storageWarning}
        </p>
      )}
      {!!analysis?.summary.missingExifCount && (
        <p className="rounded-xl border bg-muted/40 p-4 text-muted-foreground">
          รูป {analysis.summary.missingExifCount} รูปไม่มีข้อมูลเวลาถ่าย
          {analysis.parameters.similarity.missing_exif_policy === "phash"
            ? " จึงค้นหารูปคล้ายจากภาพ โดยแยกจากรูปที่มีเวลาถ่าย และยังตรวจคุณภาพได้ตามปกติ"
            : " จึงวิเคราะห์เฉพาะความคมชัดและแสง โดยไม่นำไปจัดกลุ่มรูปคล้าย"}
        </p>
      )}
      {!!analysis?.issues.length && (
        <details className="rounded-xl border p-4">
          <summary className="cursor-pointer font-medium">
            ข้ามไฟล์ {analysis.issues.length} ไฟล์
          </summary>
          <ul className="mt-3 list-disc space-y-1 pl-5">
            {analysis.issues.map((issue) => (
              <li key={issue.id}>
                {issue.filename}:{" "}
                {translateAnalysisText(
                  issue.message,
                  "ไม่สามารถประมวลผลไฟล์นี้ได้",
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
