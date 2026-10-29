"""Validate runtime settings; development metrics never affect inference."""

import json
import math
from pathlib import Path


def validate_parameters(params: dict) -> dict:
    sharp = params["sharpness"]
    exposure = params["exposure"]
    similarity = params["similarity"]
    quality = params["quality_score"]
    gap = params["recommendation"]["duplicate_quality_gap"]

    def number(value, low, high, name):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} must be between {low} and {high}")

    if sharp["method"] not in {"laplacian_score", "tenengrad_score"}:
        raise ValueError("Unknown sharpness method")
    number(sharp["threshold"], 0, float("inf"), "Sharpness threshold")
    number(exposure["low_brightness"], 0, 255, "Low brightness")
    number(exposure["high_brightness"], 0, 255, "High brightness")
    if exposure["low_brightness"] >= exposure["high_brightness"]:
        raise ValueError("Low brightness must be below high brightness")
    for key in ("dark_clip_threshold", "highlight_clip_threshold"):
        number(exposure[key], 1e-9, 1, key)
    if similarity["strategy"] not in {"exif_phash", "exif_time_or_phash"}:
        raise ValueError("Similarity strategy must be exif_phash or exif_time_or_phash")
    if similarity.get("missing_exif_policy", "strict") not in {"strict", "phash"}:
        raise ValueError("Missing EXIF policy must be strict or phash")
    if similarity.get("linkage", "complete") not in {"complete", "average"}:
        raise ValueError("Similarity linkage must be complete or average")
    if similarity.get("ssim_threshold") is not None:
        raise ValueError(
            "Legacy SSIM threshold detected; use the latest EXIF+pHash parameters"
        )
    number(similarity["phash_threshold"], 0, 64, "pHash threshold")
    if int(similarity["phash_threshold"]) != similarity["phash_threshold"]:
        raise ValueError("pHash threshold must be an integer")
    timed_phash_threshold = similarity.get("timed_phash_threshold")
    if timed_phash_threshold is not None:
        number(timed_phash_threshold, 0, 64, "Timed pHash threshold")
        if int(timed_phash_threshold) != timed_phash_threshold:
            raise ValueError("Timed pHash threshold must be an integer")
    # Time-only grouping and the legacy refinements need a finite base time window.
    number(similarity.get("exif_time_window_seconds"), 0, float("inf"), "EXIF window")
    for key in ("sharpness_weight", "exposure_weight"):
        number(quality[key], 0, 1, key)
    if not math.isclose(
        sum(quality[k] for k in ("sharpness_weight", "exposure_weight")),
        1.0,
        abs_tol=1e-6,
    ):
        raise ValueError("Quality weights must sum to 1")
    number(gap, 0, 100, "Quality gap")
    number(
        params["recommendation"].get("best_shot_tie_margin", 2.0),
        0,
        float("inf"),
        "Best Shot tie margin",
    )
    return params


def load_parameters(path: Path) -> dict:
    selected = json.loads(path.read_text(encoding="utf-8"))
    # Same backward-compatible defaults as load_selected_parameters in the notebook.
    # Add only in memory; never overwrite the user's JSON.
    selected["similarity"].setdefault("linkage", "complete")
    selected["similarity"].setdefault("missing_exif_policy", "strict")
    selected["recommendation"].setdefault("best_shot_tie_margin", 2.0)
    return validate_parameters(selected)
