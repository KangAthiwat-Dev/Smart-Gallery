import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export function AnalysisEmpty({
  isRestoring = false,
}: {
  isRestoring?: boolean;
}) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 text-center">
      <div>
        <h1 className="text-xl font-semibold">
          {isRestoring ? "กำลังเรียกคืนผลวิเคราะห์…" : "ยังไม่มีผลวิเคราะห์"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground" role="status">
          {isRestoring
            ? "กำลังโหลดผลล่าสุดที่บันทึกไว้ในอุปกรณ์นี้"
            : "เลือกรูปหรือโฟลเดอร์ แล้วเริ่มวิเคราะห์เพื่อดูผลที่นี่"}
        </p>
      </div>
      {!isRestoring && (
        <Link href="/" className={buttonVariants()}>
          เลือกรูป
        </Link>
      )}
    </div>
  );
}
