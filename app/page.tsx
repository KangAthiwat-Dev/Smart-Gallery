import { Sparkles } from "lucide-react";

import { PhotoUpload } from "@/components/upload/photo-upload";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-5xl space-y-10 py-6 sm:py-12">
      <section className="space-y-4 text-center">
        <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
          <Sparkles className="size-6" />
        </div>

        <div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-5xl">
            Clean up your gallery intelligently
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            Analyze photo quality, detect similar photos,
            and find the best shots without automatically
            deleting your photos.
          </p>
        </div>
      </section>

      <PhotoUpload />
    </div>
  );
}
