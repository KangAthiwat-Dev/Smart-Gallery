import Link from "next/link";
import { ArrowLeft, ImageOff } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center text-center">
      <div className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-muted">
        <ImageOff className="size-6 text-muted-foreground" />
      </div>

      <h1 className="text-2xl font-semibold tracking-tight">
        ไม่พบหน้าที่ต้องการ
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        หน้านี้ไม่พร้อมใช้งาน คุณสามารถกลับไปดูผลวิเคราะห์ในคลังรูปได้
      </p>

      <Link
        href="/gallery"
        aria-label="กลับไปคลังรูป"
        title="กลับไปคลังรูป"
        className={buttonVariants({
          variant: "outline",
          size: "icon",
          className: "mt-6 size-11 rounded-full",
        })}
      >
        <ArrowLeft aria-hidden="true" />
      </Link>
    </div>
  );
}
