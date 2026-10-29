export type Recommendation = "KEEP" | "REVIEW" | "RECOMMEND_DELETE";

export interface ExposureMetrics {
  brightnessMean: number;
  darkClippingRatio: number;
  highlightClippingRatio: number;
}

export interface PhotoAnalysis {
  id: string;
  filename: string;
  relativePath: string;
  imageUrl: string;
  sharpnessScore: number;
  exposureScore: number;
  qualityScore: number;
  sharpnessLabel: "sharp" | "blur";
  exposureLabel: "underexposed" | "normal" | "overexposed";
  exposureMetrics?: ExposureMetrics | null;
  takenAt: string | null;
  similarityGroup: string | null;
  bestShot: boolean;
  bestShotNeedsReview: boolean;
  recommendation: Recommendation;
  reasons: string[];
  fileSizeBytes: number;
  fileSizeMB: number;
  width: number;
  height: number;
}

export interface AnalysisSummary {
  totalPhotos: number;
  keepCount: number;
  reviewCount: number;
  recommendDeleteCount: number;
  estimatedStorageSavingMB: number;
  missingExifCount: number;
}

export interface AnalysisIssue {
  id: string;
  filename: string;
  message: string;
}

export interface AnalysisParameters {
  sharpness: { method: string; threshold: number };
  exposure: {
    low_brightness: number;
    high_brightness: number;
    dark_clip_threshold: number;
    highlight_clip_threshold: number;
  };
  similarity: {
    strategy: "exif_phash" | "exif_time_or_phash";
    missing_exif_policy: "strict" | "phash";
    linkage: "complete" | "average";
    phash_threshold: number;
    timed_phash_threshold?: number | null;
    exif_time_window_seconds: number | null;
  };
  quality_score: { sharpness_weight: number; exposure_weight: number };
  recommendation: {
    duplicate_quality_gap: number;
    best_shot_tie_margin: number;
  };
}

export interface AnalysisResponse {
  photos: PhotoAnalysis[];
  summary: AnalysisSummary;
  issues: AnalysisIssue[];
  parameters: AnalysisParameters;
}

export interface AnalysisSession extends AnalysisResponse {
  completedAt: string;
}

export interface SimilarityGroup {
  id: string;
  photos: PhotoAnalysis[];
}
