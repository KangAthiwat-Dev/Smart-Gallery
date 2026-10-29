from typing import Literal
from pydantic import BaseModel

Recommendation = Literal["KEEP", "REVIEW", "RECOMMEND_DELETE"]


class ExposureMetrics(BaseModel):
    brightnessMean: float
    darkClippingRatio: float
    highlightClippingRatio: float


class PhotoAnalysis(BaseModel):
    id: str
    filename: str
    relativePath: str
    imageUrl: str
    sharpnessScore: float
    exposureScore: float
    qualityScore: float
    sharpnessLabel: Literal["sharp", "blur"]
    exposureLabel: Literal["underexposed", "normal", "overexposed"]
    exposureMetrics: ExposureMetrics | None = None
    takenAt: str | None
    similarityGroup: str | None
    bestShot: bool
    bestShotNeedsReview: bool
    recommendation: Recommendation
    reasons: list[str]
    fileSizeBytes: int
    fileSizeMB: float
    width: int
    height: int


class AnalysisSummary(BaseModel):
    totalPhotos: int
    keepCount: int
    reviewCount: int
    recommendDeleteCount: int
    estimatedStorageSavingMB: float
    missingExifCount: int


class AnalysisIssue(BaseModel):
    id: str
    filename: str
    message: str


class AnalysisResponse(BaseModel):
    photos: list[PhotoAnalysis]
    summary: AnalysisSummary
    issues: list[AnalysisIssue]
    parameters: dict
