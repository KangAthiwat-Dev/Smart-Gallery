"use client";

import { Star } from "lucide-react";

import { PhotoCard } from "@/components/photo-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { AnalysisEmpty } from "@/components/analysis-empty";
import { AnalysisNotices } from "@/components/analysis-notices";
import { useAnalysis } from "@/contexts/analysis-context";
import type { PhotoAnalysis } from "@/types/analysis";

export default function GroupsPage() {
  const { analysis, isRestoring } = useAnalysis();
  if (isRestoring || !analysis)
    return <AnalysisEmpty isRestoring={isRestoring} />;
  const grouped = new Map<string, PhotoAnalysis[]>();
  for (const photo of analysis.photos) {
    if (photo.similarityGroup) {
      const members = grouped.get(photo.similarityGroup) || [];
      members.push(photo);
      grouped.set(photo.similarityGroup, members);
    }
  }
  const similarityGroups = Array.from(grouped, ([id, photos]) => ({
    id,
    photos,
  }));
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">กลุ่มรูปคล้าย</h1>

        <p className="text-sm text-muted-foreground">
          ดูรูปที่ถ่ายใกล้กันหรือคล้ายกัน และเลือกรูปที่ต้องการเก็บ
        </p>
      </header>

      <AnalysisNotices />
      {!similarityGroups.length && (
        <p className="rounded-xl border p-8 text-center text-sm text-muted-foreground">
          ไม่พบกลุ่มรูปคล้ายตามเกณฑ์ที่ใช้ในรอบนี้
          คุณยังสามารถดูรูปทั้งหมดได้ในคลังรูป
        </p>
      )}

      <div className="space-y-6">
        {similarityGroups.map((group) => {
          const bestShot = group.photos.find((photo) => photo.bestShot);

          return (
            <Card key={group.id}>
              <CardHeader className="flex flex-wrap items-start justify-between gap-3 sm:flex-row sm:items-center">
                <div>
                  <h2 className="font-semibold">กลุ่ม {group.id}</h2>

                  <p className="text-sm text-muted-foreground">
                    ทั้งหมด {group.photos.length} รูป
                  </p>
                </div>

                {bestShot && (
                  <Badge variant="secondary">
                    <Star className="mr-1 size-3 fill-current" />
                    {bestShot.filename}
                    {(bestShot.bestShotNeedsReview ||
                      bestShot.recommendation === "REVIEW") &&
                      " · รอตรวจสอบ"}
                  </Badge>
                )}
              </CardHeader>

              <CardContent>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {group.photos.map((photo) => (
                    <PhotoCard
                      key={photo.id}
                      photo={photo}
                      returnTo="/groups"
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
