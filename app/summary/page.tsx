import {
  HardDrive,
  Images,
  ShieldCheck,
  TriangleAlert,
  Trash2,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { photos } from "@/data/mock-data";

export default function SummaryPage() {
  const keep = photos.filter(
    (photo) => photo.recommendation === "KEEP"
  );

  const review = photos.filter(
    (photo) => photo.recommendation === "REVIEW"
  );

  const deleteCandidates = photos.filter(
    (photo) =>
      photo.recommendation === "RECOMMEND_DELETE"
  );

  const estimatedSaving = deleteCandidates.reduce(
    (total, photo) => total + photo.fileSizeMB,
    0
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">
          Analysis Summary
        </h1>

        <p className="text-sm text-muted-foreground">
          Overview of the current gallery analysis.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Analyzed"
          value={photos.length}
          icon={<Images />}
        />

        <SummaryCard
          title="Keep"
          value={keep.length}
          icon={<ShieldCheck />}
        />

        <SummaryCard
          title="Review"
          value={review.length}
          icon={<TriangleAlert />}
        />

        <SummaryCard
          title="Delete candidates"
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
              Estimated storage saving
            </p>

            <p className="text-3xl font-semibold">
              {estimatedSaving.toFixed(1)} MB
            </p>
          </div>
        </CardContent>
      </Card>

      <p className="text-sm text-muted-foreground">
        The system only recommends photos. No photo is deleted
        automatically.
      </p>
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
          <p className="text-sm text-muted-foreground">
            {title}
          </p>

          <p className="text-3xl font-semibold">{value}</p>
        </div>

        <div className="text-muted-foreground [&>svg]:size-5">
          {icon}
        </div>
      </CardContent>
    </Card>
  );
}
