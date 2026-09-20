import type {
  PhotoAnalysis,
  SimilarityGroup,
} from "@/types/analysis";

export const photos: PhotoAnalysis[] = [
  {
    id: "1",
    filename: "IMG_1001.jpg",
    imageUrl: "https://picsum.photos/seed/gallery-1/800/1000",
    sharpnessScore: 94,
    exposureScore: 88,
    qualityScore: 91,
    similarityGroup: "G001",
    bestShot: true,
    recommendation: "KEEP",
    reasons: [
      "High sharpness score",
      "Exposure is within normal range",
      "Best shot in similar group",
    ],
    fileSizeMB: 4.8,
  },
  {
    id: "2",
    filename: "IMG_1002.jpg",
    imageUrl: "https://picsum.photos/seed/gallery-2/800/1000",
    sharpnessScore: 62,
    exposureScore: 85,
    qualityScore: 71,
    similarityGroup: "G001",
    bestShot: false,
    recommendation: "RECOMMEND_DELETE",
    reasons: [
      "Similar to IMG_1001.jpg",
      "Lower sharpness than best shot",
    ],
    fileSizeMB: 4.6,
  },
  {
    id: "3",
    filename: "IMG_1003.jpg",
    imageUrl: "https://picsum.photos/seed/gallery-3/800/1000",
    sharpnessScore: 78,
    exposureScore: 82,
    qualityScore: 80,
    similarityGroup: "G001",
    bestShot: false,
    recommendation: "REVIEW",
    reasons: [
      "Similar image detected",
      "Quality is acceptable but not the best shot",
    ],
    fileSizeMB: 5.1,
  },
  {
    id: "4",
    filename: "IMG_2041.jpg",
    imageUrl: "https://picsum.photos/seed/gallery-4/800/1000",
    sharpnessScore: 91,
    exposureScore: 92,
    qualityScore: 92,
    similarityGroup: null,
    bestShot: false,
    recommendation: "KEEP",
    reasons: [
      "Sharp image",
      "Normal exposure",
      "No similar image detected",
    ],
    fileSizeMB: 5.4,
  },
  {
    id: "5",
    filename: "IMG_3021.jpg",
    imageUrl: "https://picsum.photos/seed/gallery-5/800/1000",
    sharpnessScore: 40,
    exposureScore: 74,
    qualityScore: 52,
    similarityGroup: null,
    bestShot: false,
    recommendation: "REVIEW",
    reasons: [
      "Possible blur detected",
      "Unique image — manual review recommended",
    ],
    fileSizeMB: 3.9,
  },
  {
    id: "6",
    filename: "IMG_4001.jpg",
    imageUrl: "https://picsum.photos/seed/gallery-6/800/1000",
    sharpnessScore: 82,
    exposureScore: 31,
    qualityScore: 58,
    similarityGroup: null,
    bestShot: false,
    recommendation: "REVIEW",
    reasons: [
      "Low exposure score",
      "Possible underexposure",
      "Unique image — not automatically recommended for deletion",
    ],
    fileSizeMB: 4.1,
  },
];

export const similarityGroups: SimilarityGroup[] = [
  {
    id: "G001",
    photos: photos.filter(
      (photo) => photo.similarityGroup === "G001"
    ),
  },
];
