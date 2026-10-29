// Translate presentation text only. API values and notebook algorithms stay unchanged.
const analysisText: Record<string, string> = {
  "Possible blur detected": "รูปอาจเบลอ",
  "Sharpness is acceptable": "ความคมชัดอยู่ในเกณฑ์ที่ยอมรับได้",
  "Possible underexposed": "รูปอาจมืดเกินไป",
  "Possible overexposed": "รูปอาจสว่างเกินไป",
  "Exposure is within the normal range": "แสงอยู่ในช่วงปกติ",
  "Provisional best shot; near-tied quality — review composition":
    "รูปนี้ได้คะแนนสูงสุดเบื้องต้น แต่คะแนนใกล้เคียงกัน ควรตรวจสอบองค์ประกอบภาพ",
  "Best-shot scores are too close to recommend deletion":
    "คะแนนของรูปที่ดีที่สุดใกล้เคียงกัน จึงควรตรวจสอบก่อนลบ",
  "Best shot in a similar-photo group":
    "เป็นรูปที่ได้คะแนนสูงสุดในกลุ่มรูปคล้าย",
  "Similar photo exists with a higher quality score":
    "มีรูปคล้ายกันที่ได้คะแนนคุณภาพสูงกว่า",
  "Similar photo detected, but quality is close to the best shot":
    "พบรูปคล้ายกัน แต่คุณภาพใกล้เคียงกับรูปที่ดีที่สุด",
  "No similar photo detected": "ไม่พบรูปคล้ายกัน",
  "Capture-time grouping only; pHash was not used.":
    "ใช้เวลาถ่ายช่วยค้นหารูปที่ถ่ายใกล้กัน",
  "Capture-time groups combined using the timed pHash threshold.":
    "พบรูปคล้ายกัน แม้จะถ่ายห่างกัน",
  "Best shot in a timed-photo pHash group":
    "เป็นรูปที่ได้คะแนนสูงสุดในกลุ่มรูปคล้าย",
  "Timed-photo pHash group contains a higher quality photo":
    "มีรูปคล้ายกันที่ได้คะแนนคุณภาพสูงกว่า",
  "Timed-photo pHash group detected, but quality is close to the best shot":
    "พบรูปคล้ายกัน แต่คุณภาพใกล้เคียงกับรูปที่ดีที่สุด",
  "Best shot in a capture-time group":
    "เป็นรูปที่ได้คะแนนสูงสุดในกลุ่มที่ถ่ายใกล้กัน",
  "Photo in the same capture-time group has a higher quality score":
    "มีรูปในกลุ่มที่ถ่ายใกล้กันได้คะแนนคุณภาพสูงกว่า",
  "Capture-time group detected, but quality is close to the best shot":
    "พบรูปที่ถ่ายใกล้กัน แต่คุณภาพใกล้เคียงกับรูปที่ดีที่สุด",
  "No other photo grouped within the capture-time window":
    "ไม่มีรูปอื่นอยู่ในกลุ่มช่วงเวลาถ่ายเดียวกัน",
  "Unique image — manual review recommended":
    "รูปนี้ไม่อยู่ในกลุ่มรูปคล้าย ควรตรวจสอบด้วยตนเอง",
  "Merged groups require manual verification":
    "กลุ่มที่รวมเข้าด้วยกันต้องตรวจสอบด้วยตนเอง",
  "Previously best in a separate group: review before deletion":
    "รูปนี้เคยเป็นรูปที่ดีที่สุดของกลุ่มเดิม ควรตรวจสอบก่อนลบ",
  "Group merge uncertain: verify before deletion":
    "การรวมกลุ่มยังไม่แน่ชัด ควรตรวจสอบก่อนลบ",
  "Rescued similarity match: confirm group manually":
    "รูปนี้อาจอยู่ในกลุ่มเดียวกัน ควรตรวจสอบก่อนตัดสินใจ",
  "Uncertain rescued group: manual review required":
    "กลุ่มที่เพิ่มรูปตกหล่นยังไม่แน่ชัด ต้องตรวจสอบด้วยตนเอง",
  "Insufficient original-group similarity evidence":
    "หลักฐานความคล้ายจากสมาชิกกลุ่มเดิมยังไม่เพียงพอ",
  "Missing EXIF timestamp — excluded from similarity grouping (strict EXIF).":
    "รูปนี้ไม่มีข้อมูลเวลาถ่าย จึงยังไม่จัดเข้ากลุ่มรูปคล้าย",
  "Missing EXIF timestamp — pHash comparison is limited to other photos without timestamps.":
    "รูปนี้ไม่มีข้อมูลเวลาถ่าย จึงค้นหารูปคล้ายจากภาพ โดยเทียบกับรูปที่ไม่มีเวลาเช่นกัน",
  "Unsupported image format.": "ไม่รองรับไฟล์รูปประเภทนี้",
  "Could not decode this image. It may be damaged or unsupported.":
    "อ่านรูปนี้ไม่ได้ ไฟล์อาจเสียหายหรือเป็นประเภทที่ไม่รองรับ",
  "No readable images were found.": "ไม่พบไฟล์รูปที่อ่านได้",
  "Image analysis failed. Check the backend logs.":
    "วิเคราะห์รูปไม่สำเร็จ กรุณาตรวจสอบระบบวิเคราะห์แล้วลองอีกครั้ง",
  "Invalid image manifest.": "ข้อมูลรายการรูปไม่ถูกต้อง กรุณาเลือกรูปใหม่",
  "Manifest must match the uploaded files.":
    "รายการรูปไม่ตรงกับไฟล์ที่ส่ง กรุณาเลือกรูปใหม่",
  "Invalid image entry.": "ข้อมูลรูปไม่ถูกต้อง กรุณาเลือกรูปใหม่",
  "Each image requires a valid ID.": "รหัสรูปไม่ถูกต้อง กรุณาเลือกรูปใหม่",
  "Image IDs must be unique.": "พบรหัสรูปซ้ำ กรุณาเลือกรูปใหม่",
  "Each image requires a relative path.":
    "ข้อมูลตำแหน่งไฟล์ไม่ครบ กรุณาเลือกรูปใหม่",
  "The selection exceeds the 200 MB total limit.": "ขนาดรวมของไฟล์เกิน 200 MB",
};

export function translateAnalysisText(
  value: string,
  fallback = "โปรดตรวจสอบรูปนี้เพิ่มเติม",
) {
  if (analysisText[value]) return analysisText[value];
  const count = value.match(/^Select between 1 and (\d+) images\.$/);
  if (count) return `กรุณาเลือกรูปตั้งแต่ 1 ถึง ${count[1]} รูป`;
  const oversized = value.match(/^(.*) exceeds the 30 MB file limit\.$/);
  if (oversized) return `${oversized[1]} มีขนาดเกิน 30 MB`;
  return /[ก-๙]/.test(value) ? value : fallback;
}

export const sharpnessLabels = { sharp: "คมชัด", blur: "อาจเบลอ" };
export const exposureLabels = {
  underexposed: "มืดเกินไป",
  normal: "แสงปกติ",
  overexposed: "สว่างเกินไป",
};
export const sharpnessMethodLabels: Record<string, string> = {
  laplacian_score: "Variance of Laplacian",
  tenengrad_score: "Tenengrad",
};

export function formatBytes(bytes: number) {
  const units = ["B", "KB", "MB", "GB"];
  const index =
    bytes > 0
      ? Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
      : 0;
  return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

export function formatThaiDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "ไม่ระบุ"
    : new Intl.DateTimeFormat("th-TH", {
        dateStyle: "medium",
        timeStyle: "medium",
      }).format(date);
}
