"use client";

import { useState } from "react";

import { PhotoCard } from "@/components/photo-card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { photos } from "@/data/mock-data";
import type { Recommendation } from "@/types/analysis";

type Filter =
  | "ALL"
  | Recommendation;

export default function GalleryPage() {
  const [filter, setFilter] = useState<Filter>("ALL");

  const filteredPhotos =
    filter === "ALL"
      ? photos
      : photos.filter(
          (photo) => photo.recommendation === filter
        );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">
          Gallery
        </h1>

        <p className="text-sm text-muted-foreground">
          {photos.length} analyzed photos
        </p>
      </header>

      <Tabs
        value={filter}
        onValueChange={(value) => setFilter(value as Filter)}
      >
        <TabsList className="h-auto flex-wrap">
          <TabsTrigger value="ALL">All</TabsTrigger>
          <TabsTrigger value="KEEP">Keep</TabsTrigger>
          <TabsTrigger value="REVIEW">Review</TabsTrigger>
          <TabsTrigger value="RECOMMEND_DELETE">
            Delete
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {filteredPhotos.map((photo) => (
          <PhotoCard key={photo.id} photo={photo} />
        ))}
      </div>

      {filteredPhotos.length === 0 && (
        <div className="py-20 text-center text-sm text-muted-foreground">
          No photos in this category.
        </div>
      )}
    </div>
  );
}
