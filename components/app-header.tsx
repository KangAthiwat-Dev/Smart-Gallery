import Link from "next/link";
import { Images, Layers3, ChartNoAxesColumnIncreasing } from "lucide-react";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
        <Link
          href="/"
          className="rounded-md font-semibold tracking-tight outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          Smart Gallery
        </Link>

        <nav aria-label="เมนูหลัก" className="flex items-center gap-1">
          <Link
            href="/gallery"
            aria-label="คลังรูป"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm outline-none hover:bg-muted focus-visible:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <Images className="size-4" />
            <span className="hidden sm:inline">คลังรูป</span>
          </Link>

          <Link
            href="/groups"
            aria-label="กลุ่มรูปคล้าย"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm outline-none hover:bg-muted focus-visible:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <Layers3 className="size-4" />
            <span className="hidden sm:inline">กลุ่มรูปคล้าย</span>
          </Link>

          <Link
            href="/summary"
            aria-label="สรุปผล"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm outline-none hover:bg-muted focus-visible:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <ChartNoAxesColumnIncreasing className="size-4" />
            <span className="hidden sm:inline">สรุปผล</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
