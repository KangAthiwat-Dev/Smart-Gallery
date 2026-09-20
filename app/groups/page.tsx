import { Star } from "lucide-react";

import { PhotoCard } from "@/components/photo-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { similarityGroups } from "@/data/mock-data";

export default function GroupsPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">
          Similar Photos
        </h1>

        <p className="text-sm text-muted-foreground">
          Review detected groups and their best shots.
        </p>
      </header>

      <div className="space-y-6">
        {similarityGroups.map((group) => {
          const bestShot = group.photos.find(
            (photo) => photo.bestShot
          );

          return (
            <Card key={group.id}>
              <CardHeader className="flex-row items-center justify-between">
                <div>
                  <h2 className="font-semibold">
                    Group {group.id}
                  </h2>

                  <p className="text-sm text-muted-foreground">
                    {group.photos.length} similar photos
                  </p>
                </div>

                {bestShot && (
                  <Badge variant="secondary">
                    <Star className="mr-1 size-3 fill-current" />
                    {bestShot.filename}
                  </Badge>
                )}
              </CardHeader>

              <CardContent>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {group.photos.map((photo) => (
                    <PhotoCard
                      key={photo.id}
                      photo={photo}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
