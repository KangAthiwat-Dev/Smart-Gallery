from __future__ import annotations

import base64
import io
import json
import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from app.parameters import load_parameters
from app.schemas import AnalysisIssue, AnalysisResponse, AnalysisSummary, PhotoAnalysis
from app.services.pipeline import extract_features, load_image, analyze_features

BASE_DIR = Path(__file__).resolve().parent.parent
PARAMS = load_parameters(BASE_DIR / "config" / "best_parameters.json")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".heic", ".heif"}
MAX_FILES = 200
MAX_FILE_BYTES = 30 * 1024 * 1024
MAX_TOTAL_BYTES = 200 * 1024 * 1024
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Gallery Image Analysis API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    legacy_refinements = PARAMS["similarity"]["strategy"] == "exif_phash"
    return {
        "status": "ok",
        "similarityStrategy": PARAMS["similarity"]["strategy"],
        "missingExifPolicy": PARAMS["similarity"].get("missing_exif_policy", "strict"),
        "linkage": PARAMS["similarity"]["linkage"],
        "singletonRescue": legacy_refinements,
        "groupMerge": legacy_refinements,
        "timedPhashThreshold": (
            PARAMS["similarity"].get("timed_phash_threshold")
            if not legacy_refinements
            else None
        ),
        "maxFiles": MAX_FILES,
    }


def jpeg_preview(path: Path) -> str:
    # Convert HEIC and all other supported formats to browser-compatible JPEG.
    rgb = load_image(path)["rgb"]
    buffer = io.BytesIO()
    Image.fromarray(rgb).save(buffer, format="JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode(
        "ascii"
    )


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(
    files: list[UploadFile] = File(...),
    manifest: str = Form(...),
):
    # A synchronous handler runs CPU work in FastAPI's thread pool.
    try:
        try:
            entries = json.loads(manifest)
        except (ValueError, TypeError) as exc:
            raise HTTPException(400, "Invalid image manifest.") from exc
        if not files or len(files) > MAX_FILES:
            raise HTTPException(400, f"Select between 1 and {MAX_FILES} images.")
        if not isinstance(entries, list) or len(entries) != len(files):
            raise HTTPException(400, "Manifest must match the uploaded files.")
        ids = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise HTTPException(400, "Invalid image entry.")
            image_id = entry.get("id")
            if not isinstance(image_id, str) or not image_id or len(image_id) > 100:
                raise HTTPException(400, "Each image requires a valid ID.")
            if image_id in ids:
                raise HTTPException(400, "Image IDs must be unique.")
            ids.add(image_id)
            if not isinstance(entry.get("relativePath"), str):
                raise HTTPException(400, "Each image requires a relative path.")

        issues = []
        features = []
        metadata = {}
        total_bytes = 0
        with tempfile.TemporaryDirectory(prefix="smart-gallery-") as temp_dir:
            for index, (upload, entry) in enumerate(zip(files, entries)):
                filename = Path((upload.filename or "image").replace("\\", "/")).name
                suffix = Path(filename).suffix.lower()
                if suffix not in SUPPORTED_EXTENSIONS:
                    issues.append(
                        AnalysisIssue(
                            id=entry["id"],
                            filename=filename,
                            message="Unsupported image format.",
                        )
                    )
                    continue
                path = Path(temp_dir) / f"{index:04d}{suffix}"
                size = 0
                with path.open("wb") as destination:
                    while chunk := upload.file.read(1024 * 1024):
                        size += len(chunk)
                        total_bytes += len(chunk)
                        if size > MAX_FILE_BYTES:
                            raise HTTPException(
                                413, f"{filename} exceeds the 30 MB file limit."
                            )
                        if total_bytes > MAX_TOTAL_BYTES:
                            raise HTTPException(
                                413, "The selection exceeds the 200 MB total limit."
                            )
                        destination.write(chunk)
                try:
                    feature = extract_features(path)
                    preview = jpeg_preview(path)
                except (
                    UnidentifiedImageError,
                    OSError,
                    ValueError,
                    Image.DecompressionBombError,
                ):
                    issues.append(
                        AnalysisIssue(
                            id=entry["id"],
                            filename=filename,
                            message="Could not decode this image. It may be damaged or unsupported.",
                        )
                    )
                    continue
                feature["filename"] = filename
                features.append(feature)
                metadata[str(path)] = (entry, preview)

            if not features:
                raise HTTPException(
                    422,
                    {
                        "message": "No readable images were found.",
                        "issues": [issue.model_dump() for issue in issues],
                    },
                )

            try:
                results, _ = analyze_features(pd.DataFrame(features), PARAMS)
            except Exception as exc:
                logger.exception("Image analysis failed")
                raise HTTPException(
                    500, "Image analysis failed. Check the backend logs."
                ) from exc

            photos = []
            for _, row in results.iterrows():
                entry, preview = metadata[row["path"]]
                group = row["similarityGroup"]
                reasons = list(row["reasons"])
                taken_at = None if pd.isna(row["taken_at"]) else str(row["taken_at"])
                if taken_at is None:
                    if PARAMS["similarity"].get("missing_exif_policy") == "phash":
                        reasons.append(
                            "Missing EXIF timestamp — pHash comparison is limited to other photos without timestamps."
                        )
                    else:
                        reasons.append(
                            "Missing EXIF timestamp — excluded from similarity grouping (strict EXIF)."
                        )
                photos.append(
                    PhotoAnalysis(
                        id=entry["id"],
                        filename=row["filename"],
                        relativePath=entry["relativePath"],
                        imageUrl=preview,
                        sharpnessScore=round(float(row["sharpnessScore"]), 2),
                        exposureScore=round(float(row["exposureScore"]), 2),
                        qualityScore=round(float(row["qualityScore"]), 2),
                        sharpnessLabel=row["sharpness_label"],
                        exposureLabel=row["exposure_label_pred"],
                        exposureMetrics={
                            "brightnessMean": float(row["brightness_mean"]),
                            "darkClippingRatio": float(row["dark_clipping_ratio"]),
                            "highlightClippingRatio": float(
                                row["highlight_clipping_ratio"]
                            ),
                        },
                        takenAt=taken_at,
                        similarityGroup=str(group) if pd.notna(group) else None,
                        bestShot=bool(row["bestShot"]),
                        bestShotNeedsReview=bool(row["bestShotNeedsReview"]),
                        recommendation=row["recommendation"],
                        reasons=reasons,
                        fileSizeBytes=int(row["file_size_bytes"]),
                        fileSizeMB=float(row["file_size_bytes"]) / (1024 * 1024),
                        width=int(row["original_width"]),
                        height=int(row["original_height"]),
                    )
                )
        return AnalysisResponse(
            photos=photos,
            summary=AnalysisSummary(
                totalPhotos=len(photos),
                keepCount=sum(p.recommendation == "KEEP" for p in photos),
                reviewCount=sum(p.recommendation == "REVIEW" for p in photos),
                recommendDeleteCount=sum(
                    p.recommendation == "RECOMMEND_DELETE" for p in photos
                ),
                estimatedStorageSavingMB=sum(
                    p.fileSizeBytes
                    for p in photos
                    if p.recommendation == "RECOMMEND_DELETE"
                )
                / (1024 * 1024),
                missingExifCount=sum(p.takenAt is None for p in photos),
            ),
            issues=issues,
            parameters=PARAMS,
        )
    finally:
        for upload in files:
            upload.file.close()
