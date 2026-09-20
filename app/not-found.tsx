import Link from "next/link";
import { ImageOff } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center text-center">
      <div className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-muted">
        <ImageOff className="size-6 text-muted-foreground" />
      </div>

      <h1 className="text-2xl font-semibold tracking-tight">Photo not found</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        This photo is not included in the current sample analysis.
      </p>

      <Link href="/gallery" className={buttonVariants({ className: "mt-6" })}>
        Back to Gallery
      </Link>
    </div>
  );
}
