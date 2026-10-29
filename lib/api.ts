import type { AnalysisResponse } from "@/types/analysis";
import { translateAnalysisText } from "@/lib/locale-th";

export type AnalysisInput = { id: string; file: File; relativePath: string };

export const MAX_FILES = 200;
export const MAX_FILE_BYTES = 30 * 1024 * 1024;
export const MAX_TOTAL_BYTES = 200 * 1024 * 1024;
export const SUPPORTED_EXTENSIONS = /\.(jpe?g|png|bmp|webp|heic|heif)$/i;

export async function analyzePhotos(
  photos: AnalysisInput[],
  signal?: AbortSignal,
): Promise<AnalysisResponse> {
  const formData = new FormData();
  photos.forEach(({ file }) => formData.append("files", file));
  formData.append(
    "manifest",
    JSON.stringify(
      photos.map(({ id, relativePath }) => ({ id, relativePath })),
    ),
  );

  const baseUrl = (
    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/analyze`, {
      method: "POST",
      body: formData,
      signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new Error(
      "ติดต่อระบบวิเคราะห์ไม่ได้ กรุณาเปิดระบบวิเคราะห์แล้วลองอีกครั้ง",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message = translateAnalysisText(
      typeof detail === "string" ? detail : detail?.message || "",
      `วิเคราะห์ไม่สำเร็จ (รหัส ${response.status}) กรุณาลองอีกครั้ง`,
    );
    const issues = Array.isArray(detail?.issues)
      ? detail.issues
          .map(
            (issue: { filename: string; message: string }) =>
              `${issue.filename}: ${translateAnalysisText(issue.message, "ไม่สามารถประมวลผลไฟล์นี้ได้")}`,
          )
          .join(" ")
      : "";
    throw new Error([message, issues].filter(Boolean).join(" "));
  }
  const result: AnalysisResponse = await response.json();
  const expectedIds = new Set(photos.map((photo) => photo.id));
  const returnedIds = new Set<string>();
  for (const photo of result.photos) {
    if (!expectedIds.has(photo.id) || returnedIds.has(photo.id)) {
      throw new Error(
        "ข้อมูลรูปที่ส่งกลับมาไม่ตรงกับรายการที่เลือก กรุณาลองใหม่",
      );
    }
    returnedIds.add(photo.id);
  }
  return result;
}
