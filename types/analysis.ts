export type Recommendation =
  | "KEEP"
  | "REVIEW"
  | "RECOMMEND_DELETE";

export interface PhotoAnalysis {
  id: string;
  filename: string;
  imageUrl: string;

  sharpnessScore: number;
  exposureScore: number;
  qualityScore: number;

  similarityGroup: string | null;
  bestShot: boolean;

  recommendation: Recommendation;
  reasons: string[];

  fileSizeMB: number;
}

export interface SimilarityGroup {
  id: string;
  photos: PhotoAnalysis[];
}
