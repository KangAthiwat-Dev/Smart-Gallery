from __future__ import annotations

from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import cv2 as cv
import imagehash
import numpy as np
import pandas as pd
from PIL import ExifTags, Image, ImageOps
from pillow_heif import register_heif_opener
from sklearn.cluster import AgglomerativeClustering

register_heif_opener()

MAX_SIDE = 1024
DARK_PIXEL_MAX = 10
HIGHLIGHT_PIXEL_MIN = 245


def parse_exif_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            pass

    return None


def load_image(path: Path, max_side: int = MAX_SIDE) -> dict[str, Any]:
    with Image.open(path) as pil:
        exif_raw = pil.getexif()
        exif = (
            {ExifTags.TAGS.get(k, str(k)): v for k, v in exif_raw.items()}
            if exif_raw
            else {}
        )
        if exif_raw:
            # Phone/camera DateTimeOriginal commonly lives in the Exif sub-IFD.
            capture_exif = exif_raw.get_ifd(ExifTags.IFD.Exif)
            exif.update(
                {
                    ExifTags.TAGS.get(key, str(key)): value
                    for key, value in capture_exif.items()
                }
            )

        pil = ImageOps.exif_transpose(pil).convert("RGB")
        original_width, original_height = pil.size
        rgb = np.array(pil)

    if max(rgb.shape[:2]) > max_side:
        scale = max_side / max(rgb.shape[:2])
        new_size = (
            max(1, round(rgb.shape[1] * scale)),
            max(1, round(rgb.shape[0] * scale)),
        )
        rgb = cv.resize(rgb, new_size, interpolation=cv.INTER_AREA)

    taken_at = parse_exif_datetime(
        exif.get("DateTimeOriginal")
        or exif.get("DateTimeDigitized")
        or exif.get("DateTime")
    )

    return {
        "path": str(path),
        "filename": path.name,
        "rgb": rgb,
        "file_size_bytes": path.stat().st_size,
        "taken_at": taken_at,
        "original_width": original_width,
        "original_height": original_height,
    }


def to_gray(rgb: np.ndarray) -> np.ndarray:
    return cv.cvtColor(rgb, cv.COLOR_RGB2GRAY)


def sharpness_features(rgb: np.ndarray) -> dict[str, float]:
    gray = to_gray(rgb).astype(np.float64)

    lap = cv.Laplacian(gray, cv.CV_64F)
    gx = cv.Sobel(gray, cv.CV_64F, 1, 0, ksize=3)
    gy = cv.Sobel(gray, cv.CV_64F, 0, 1, ksize=3)

    return {
        "laplacian_score": float(lap.var()),
        "tenengrad_score": float(np.mean(gx**2 + gy**2)),
    }


def exposure_features(rgb: np.ndarray) -> dict[str, float]:
    y = cv.cvtColor(rgb, cv.COLOR_RGB2YCrCb)[:, :, 0]

    return {
        "brightness_mean": float(np.mean(y)),
        "brightness_median": float(np.median(y)),
        "dark_clipping_ratio": float(np.mean(y <= DARK_PIXEL_MAX)),
        "highlight_clipping_ratio": float(np.mean(y >= HIGHLIGHT_PIXEL_MIN)),
    }


def phash_value(rgb: np.ndarray):
    return imagehash.phash(Image.fromarray(rgb), hash_size=8)


def extract_features(path: Path) -> dict[str, Any]:
    item = load_image(path)
    sharp = sharpness_features(item["rgb"])
    exposure = exposure_features(item["rgb"])

    return {
        "filename": item["filename"],
        "path": item["path"],
        "file_size_bytes": item["file_size_bytes"],
        "taken_at": (item["taken_at"].isoformat() if item["taken_at"] else None),
        "original_width": item["original_width"],
        "original_height": item["original_height"],
        **sharp,
        **exposure,
        "phash": str(phash_value(item["rgb"])),
    }


def classify_sharpness(
    row: pd.Series,
    params: dict[str, Any],
) -> str:
    cfg = params["sharpness"]

    return "sharp" if float(row[cfg["method"]]) >= float(cfg["threshold"]) else "blur"


def classify_exposure(
    row: pd.Series,
    params: dict[str, Any],
) -> str:
    cfg = params["exposure"]

    if (
        row["brightness_mean"] <= cfg["low_brightness"]
        or row["dark_clipping_ratio"] >= cfg["dark_clip_threshold"]
    ):
        return "underexposed"

    if (
        row["brightness_mean"] >= cfg["high_brightness"]
        or row["highlight_clipping_ratio"] >= cfg["highlight_clip_threshold"]
    ):
        return "overexposed"

    return "normal"


def sharpness_score_0_100(
    row: pd.Series,
    params: dict[str, Any],
) -> float:
    cfg = params["sharpness"]

    raw = max(0.0, float(row[cfg["method"]]))
    threshold = max(1e-9, float(cfg["threshold"]))

    return float(
        np.clip(
            100.0 * raw / (raw + threshold),
            0,
            100,
        )
    )


def exposure_score_0_100(
    row: pd.Series,
    params: dict[str, Any],
) -> float:
    cfg = params["exposure"]

    mean = float(row["brightness_mean"])
    low = float(cfg["low_brightness"])
    high = float(cfg["high_brightness"])

    if mean < low:
        brightness_score = 100.0 * max(0.0, mean / max(low, 1e-9))
    elif mean > high:
        brightness_score = 100.0 * max(
            0.0,
            (255.0 - mean) / max(255.0 - high, 1e-9),
        )
    else:
        brightness_score = 100.0

    dark_ratio = float(row["dark_clipping_ratio"])
    highlight_ratio = float(row["highlight_clipping_ratio"])

    dark_thr = max(
        float(cfg["dark_clip_threshold"]),
        1e-9,
    )
    high_thr = max(
        float(cfg["highlight_clip_threshold"]),
        1e-9,
    )

    clip_penalty = 25.0 * max(
        max(0.0, dark_ratio / dark_thr - 1.0),
        max(
            0.0,
            highlight_ratio / high_thr - 1.0,
        ),
    )

    return float(
        np.clip(
            brightness_score - clip_penalty,
            0,
            100,
        )
    )


def add_quality_scores(
    df: pd.DataFrame,
    params: dict[str, Any],
) -> pd.DataFrame:
    result = df.copy()

    result["sharpness_label"] = result.apply(
        lambda row: classify_sharpness(row, params),
        axis=1,
    )
    result["exposure_label_pred"] = result.apply(
        lambda row: classify_exposure(row, params),
        axis=1,
    )
    result["sharpnessScore"] = result.apply(
        lambda row: sharpness_score_0_100(row, params),
        axis=1,
    )
    result["exposureScore"] = result.apply(
        lambda row: exposure_score_0_100(row, params),
        axis=1,
    )

    sw = float(
        params["quality_score"].get(
            "sharpness_weight",
            0.60,
        )
    )
    ew = float(
        params["quality_score"].get(
            "exposure_weight",
            0.40,
        )
    )

    total = sw + ew

    result["qualityScore"] = (
        sw * result["sharpnessScore"] + ew * result["exposureScore"]
    ) / total

    return result


def _time_difference_seconds(a, b):
    ta = pd.to_datetime(a, errors="coerce")
    tb = pd.to_datetime(b, errors="coerce")
    if pd.isna(ta) or pd.isna(tb):
        return None
    return abs((ta - tb).total_seconds())


def _merge_timed_phash_groups(seed_groups, pair_distances, threshold):
    """Merge whole time groups only when every cross-group pair is eligible."""
    distances = np.zeros((len(seed_groups), len(seed_groups)), dtype=float)
    for a, b in combinations(range(len(seed_groups)), 2):
        distance = max(
            pair_distances[tuple(sorted((i, j)))]
            for i in seed_groups[a]
            for j in seed_groups[b]
        )
        distances[a, b] = distances[b, a] = distance
    labels = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="complete",
        distance_threshold=float(threshold) + 1e-09,
    ).fit_predict(distances)
    members_by_cluster = {}
    seeds_by_cluster = {}
    for members, label in zip(seed_groups, labels):
        members_by_cluster.setdefault(label, []).extend(members)
        seeds_by_cluster[label] = seeds_by_cluster.get(label, 0) + 1
    merged_indices = {
        index
        for label, members in members_by_cluster.items()
        if seeds_by_cluster[label] > 1
        for index in members
    }
    return list(members_by_cluster.values()), merged_indices


def _build_time_or_phash_groups(df, params, missing_exif_policy):
    """Keep time groups intact, optionally bridge them using a separate pHash rule."""
    cfg = params["similarity"]
    result = df.copy().reset_index(drop=True)
    records = result.to_dict("records")
    timestamps = [pd.to_datetime(r.get("taken_at"), errors="coerce") for r in records]
    timed = [i for i, timestamp in enumerate(timestamps) if pd.notna(timestamp)]
    untimed = [i for i, timestamp in enumerate(timestamps) if pd.isna(timestamp)]
    pools = [(timed, "exif_time", float(cfg["exif_time_window_seconds"]), "complete")]
    if missing_exif_policy == "phash":
        pools.append(
            (
                untimed,
                "phash",
                float(cfg["phash_threshold"]),
                cfg.get("linkage", "complete"),
            )
        )

    clusters = []
    pair_rows = []
    timed_phash_threshold = cfg.get("timed_phash_threshold")
    timed_pair_distances = {}
    timed_hashes = {}
    result["timedPhashMatch"] = False
    for indices, strategy, threshold, linkage in pools:
        if len(indices) < 2:
            continue
        distances = np.zeros((len(indices), len(indices)), dtype=float)
        hashes = (
            [imagehash.hex_to_hash(str(records[i]["phash"])) for i in indices]
            if strategy == "phash"
            else None
        )
        for local_i, local_j in combinations(range(len(indices)), 2):
            i, j = indices[local_i], indices[local_j]
            if strategy == "exif_time":
                time_diff = abs((timestamps[i] - timestamps[j]).total_seconds())
                hamming = None
                distance = time_diff
            else:
                time_diff = None
                hamming = int(hashes[local_i] - hashes[local_j])
                distance = float(hamming)
            pair_pass = bool(distance <= threshold)
            pair_strategy = strategy
            if strategy == "exif_time" and timed_phash_threshold is not None:
                if pair_pass:
                    # Time-matched photos never have to pass pHash.
                    timed_pair_distances[i, j] = 0.0
                else:
                    for index in (i, j):
                        if index not in timed_hashes:
                            timed_hashes[index] = imagehash.hex_to_hash(
                                str(records[index]["phash"])
                            )
                    hamming = int(timed_hashes[i] - timed_hashes[j])
                    timed_pair_distances[i, j] = float(hamming)
                    pair_pass = bool(hamming <= timed_phash_threshold)
                    pair_strategy = "timed_phash"
            distances[local_i, local_j] = distances[local_j, local_i] = distance
            pair_rows.append(
                {
                    "image_a": records[i]["filename"],
                    "image_b": records[j]["filename"],
                    "strategy": pair_strategy,
                    "linkage": linkage,
                    "time_difference_seconds": time_diff,
                    "hamming_distance": hamming,
                    "is_similar": pair_pass,
                }
            )
        labels = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage=linkage,
            distance_threshold=threshold + 1e-09,
        ).fit_predict(distances)
        members_by_cluster = {}
        for index, label in zip(indices, labels):
            members_by_cluster.setdefault(label, []).append(index)
        pool_groups = list(members_by_cluster.values())
        if (
            strategy == "exif_time"
            and timed_phash_threshold is not None
            and len(pool_groups) > 1
        ):
            pool_groups, merged_indices = _merge_timed_phash_groups(
                pool_groups, timed_pair_distances, timed_phash_threshold
            )
            result.loc[sorted(merged_indices), "timedPhashMatch"] = True
        clusters.extend(members for members in pool_groups if len(members) >= 2)

    group_by_index = {}
    for number, members in enumerate(sorted(clusters, key=min), start=1):
        for index in members:
            group_by_index[index] = f"G{number:03d}"
    result["similarityGroup"] = [group_by_index.get(i) for i in range(len(result))]
    return result, pd.DataFrame(pair_rows)


def build_similarity_groups(df, params, missing_exif_policy=None):
    """Dispatch to separate time/pHash grouping or the legacy notebook strategy.

    The demo strategy uses time first, with optional pHash for out-of-window
    timed pairs. The legacy strategy
    below uses raw pHash distances and blocks time-ineligible pairs, including
    through average linkage. Both strategies keep timed and untimed pools apart.
    """
    cfg = params["similarity"]
    if missing_exif_policy is None:
        missing_exif_policy = cfg.get("missing_exif_policy", "strict")
    if missing_exif_policy not in {"strict", "phash"}:
        raise ValueError("Missing EXIF policy must be strict or phash.")
    if cfg.get("strategy") not in {"exif_phash", "exif_time_or_phash"}:
        raise ValueError(
            "Similarity strategy must be exif_phash or exif_time_or_phash."
        )
    linkage = cfg.get("linkage", "complete")
    if linkage not in ("complete", "average"):
        raise ValueError("linkage must be 'complete' or 'average'")
    if cfg["strategy"] == "exif_time_or_phash":
        return _build_time_or_phash_groups(df, params, missing_exif_policy)
    phash_thr = int(cfg["phash_threshold"])
    time_window = cfg.get("exif_time_window_seconds")
    if time_window is not None:
        time_window = float(time_window)
    records = df.to_dict("records")
    n = len(records)
    result = df.copy().reset_index(drop=True)
    result["similarityGroup"] = None
    if n < 2:
        return (result, pd.DataFrame())
    hashes = [imagehash.hex_to_hash(str(r["phash"])) for r in records]
    has_timestamp = [
        pd.notna(pd.to_datetime(r.get("taken_at"), errors="coerce")) for r in records
    ]
    blocked_distance = float((n * n + 1) * 65)
    distances = np.full((n, n), blocked_distance, dtype=float)
    np.fill_diagonal(distances, 0.0)
    pair_rows = []
    for i, j in combinations(range(n), 2):
        a, b = (records[i], records[j])
        time_diff = _time_difference_seconds(a.get("taken_at"), b.get("taken_at"))
        time_pass = time_diff is not None and (
            time_window is None or time_diff <= time_window
        )
        phash_fallback = (
            not has_timestamp[i]
            and not has_timestamp[j]
            and missing_exif_policy == "phash"
        )
        eligible = time_pass or phash_fallback
        hamming = int(hashes[i] - hashes[j])
        pair_pass = bool(eligible and hamming <= phash_thr)
        if eligible:
            distances[i, j] = float(hamming)
            distances[j, i] = float(hamming)
        pair_rows.append(
            {
                "image_a": a["filename"],
                "image_b": b["filename"],
                "strategy": "phash" if phash_fallback else "exif_phash",
                "linkage": linkage,
                "time_difference_seconds": time_diff,
                "hamming_distance": hamming,
                "is_similar": pair_pass,
            }
        )
    model = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage=linkage,
        distance_threshold=float(phash_thr) + 1e-09,
    )
    cluster_labels = model.fit_predict(distances)
    members_by_cluster = {}
    for index, cluster_id in enumerate(cluster_labels):
        members_by_cluster.setdefault(int(cluster_id), []).append(index)
    clusters = sorted(members_by_cluster.values(), key=lambda members: min(members))
    group_by_index = {}
    group_number = 1
    for members in clusters:
        if len(members) < 2:
            continue
        group_name = f"G{group_number:03d}"
        group_number += 1
        for index in members:
            group_by_index[index] = group_name
    result["similarityGroup"] = [group_by_index.get(index) for index in range(n)]
    return (result, pd.DataFrame(pair_rows))


def add_best_shot_and_recommendation(df, params):
    result = df.copy()
    result["bestShot"] = False
    result["bestShotNeedsReview"] = False
    tie_margin = float(params["recommendation"].get("best_shot_tie_margin", 2.0))
    delete_gap = float(params["recommendation"].get("duplicate_quality_gap", 5.0))
    if tie_margin < 0:
        raise ValueError("best_shot_tie_margin cannot be negative")
    grouped = result[result["similarityGroup"].notna()].groupby("similarityGroup")
    for _, group in grouped:
        ranked = group["qualityScore"].sort_values(ascending=False)
        best_idx = ranked.index[0]
        result.loc[best_idx, "bestShot"] = True
        if len(ranked) >= 2:
            score_gap = float(ranked.iloc[0] - ranked.iloc[1])
            if score_gap < tie_margin:
                near_tie_idxs = ranked.index[ranked.iloc[0] - ranked < tie_margin]
                result.loc[near_tie_idxs, "bestShotNeedsReview"] = True
    recommendations = []
    reasons_all = []
    for _, row in result.iterrows():
        reasons = []
        group_id = row["similarityGroup"]
        time_group = params["similarity"][
            "strategy"
        ] == "exif_time_or_phash" and pd.notna(
            pd.to_datetime(row.get("taken_at"), errors="coerce")
        )
        timed_phash_group = time_group and bool(row.get("timedPhashMatch", False))
        if row["sharpness_label"] == "blur":
            reasons.append("Possible blur detected")
        else:
            reasons.append("Sharpness is acceptable")
        if row["exposure_label_pred"] != "normal":
            reasons.append(f"Possible {row['exposure_label_pred']}")
        else:
            reasons.append("Exposure is within the normal range")
        if time_group:
            reasons.append(
                "Capture-time groups combined using the timed pHash threshold."
                if timed_phash_group
                else "Capture-time grouping only; pHash was not used."
            )
        if pd.notna(group_id):
            group = result[result["similarityGroup"] == group_id]
            best_quality = float(group["qualityScore"].max())
            if bool(row["bestShotNeedsReview"]):
                recommendations.append("REVIEW")
                if bool(row["bestShot"]):
                    reasons.append(
                        "Provisional best shot; near-tied quality — review composition"
                    )
                else:
                    reasons.append(
                        "Best-shot scores are too close to recommend deletion"
                    )
            elif bool(row["bestShot"]):
                recommendations.append("KEEP")
                reasons.append(
                    "Best shot in a timed-photo pHash group"
                    if timed_phash_group
                    else (
                        "Best shot in a capture-time group"
                        if time_group
                        else "Best shot in a similar-photo group"
                    )
                )
            elif best_quality - float(row["qualityScore"]) >= delete_gap:
                recommendations.append("RECOMMEND_DELETE")
                reasons.append(
                    "Timed-photo pHash group contains a higher quality photo"
                    if timed_phash_group
                    else (
                        "Photo in the same capture-time group has a higher quality score"
                        if time_group
                        else "Similar photo exists with a higher quality score"
                    )
                )
            else:
                recommendations.append("REVIEW")
                reasons.append(
                    "Timed-photo pHash group detected, but quality is close to the best shot"
                    if timed_phash_group
                    else (
                        "Capture-time group detected, but quality is close to the best shot"
                        if time_group
                        else "Similar photo detected, but quality is close to the best shot"
                    )
                )
        elif (
            row["sharpness_label"] == "sharp" and row["exposure_label_pred"] == "normal"
        ):
            recommendations.append("KEEP")
            reasons.append(
                "No other photo grouped within the capture-time window"
                if time_group
                else "No similar photo detected"
            )
        else:
            recommendations.append("REVIEW")
            reasons.append("Unique image — manual review recommended")
        reasons_all.append(reasons)
    result["recommendation"] = recommendations
    result["reasons"] = reasons_all
    return result


def rescue_borderline_singletons(grouped, params):
    original = grouped.copy().reset_index(drop=True)
    result = original.copy()
    cfg = params["similarity"]
    threshold = int(cfg["phash_threshold"])
    window = float(cfg["exif_time_window_seconds"])
    groups = original[original["similarityGroup"].notna()].groupby("similarityGroup")
    rescue_log = []
    for idx, row in original[original["similarityGroup"].isna()].iterrows():
        candidate_groups = []
        if pd.isna(row.get("phash")) or pd.isna(row.get("taken_at")):
            continue
        for group_id, members in groups:
            if len(members) < 3:
                continue
            if members["phash"].isna().any() or members["taken_at"].isna().any():
                continue
            distances = []
            time_diffs = []
            for _, member in members.iterrows():
                hd = int(
                    imagehash.hex_to_hash(str(row["phash"]))
                    - imagehash.hex_to_hash(str(member["phash"]))
                )
                dt = _time_difference_seconds(row["taken_at"], member["taken_at"])
                distances.append(hd)
                time_diffs.append(dt)
            time_ok = all((t is not None and t <= window for t in time_diffs))
            avg_ok = np.mean(distances) <= threshold + 0.5
            max_ok = max(distances) <= threshold + 5
            strong_ok = sum((d <= threshold for d in distances)) >= 2
            if time_ok and avg_ok and max_ok and strong_ok:
                candidate_groups.append(
                    {
                        "Group": group_id,
                        "Average Distance": np.mean(distances),
                        "Max Distance": max(distances),
                    }
                )
        if len(candidate_groups) == 1:
            selected = candidate_groups[0]
            result.at[idx, "similarityGroup"] = selected["Group"]
            rescue_log.append(
                {
                    "Filename": row["filename"],
                    "Assigned Group": selected["Group"],
                    "Average Distance": round(selected["Average Distance"], 2),
                    "Max Distance": selected["Max Distance"],
                }
            )
    return (result, pd.DataFrame(rescue_log))


def merge_nearby_similarity_groups(grouped, params, rescue_log=None):
    result = grouped.copy().reset_index(drop=True)
    cfg = params["similarity"]
    phash_limit = int(cfg["phash_threshold"])
    strict_time = float(cfg["exif_time_window_seconds"])
    extended_time = strict_time * 2
    original_groups = {
        group_id: members.index.tolist()
        for group_id, members in result[result["similarityGroup"].notna()].groupby(
            "similarityGroup", sort=True
        )
        if len(members) >= 2
    }
    rescued_groups = (
        set(rescue_log["Assigned Group"].tolist())
        if rescue_log is not None and (not rescue_log.empty)
        else set()
    )
    hashes = {
        idx: imagehash.hex_to_hash(str(row["phash"]))
        for idx, row in result.iterrows()
        if pd.notna(row.get("phash"))
    }
    candidates = []
    for (group_a, members_a), (group_b, members_b) in combinations(
        original_groups.items(), 2
    ):
        if group_a in rescued_groups or group_b in rescued_groups:
            continue
        all_ids = members_a + members_b
        if (
            any((i not in hashes for i in all_ids))
            or result.loc[all_ids, "taken_at"].isna().any()
        ):
            continue
        cross_distances, cross_times = ([], [])
        for i in members_a:
            for j in members_b:
                cross_distances.append(int(hashes[i] - hashes[j]))
                cross_times.append(
                    _time_difference_seconds(
                        result.at[i, "taken_at"], result.at[j, "taken_at"]
                    )
                )
        time_ok = all((t is not None and t <= extended_time for t in cross_times))
        phash_ok = all((d <= phash_limit for d in cross_distances))
        strict_links = sum(
            (
                d <= phash_limit and t is not None and (t <= strict_time)
                for d, t in zip(cross_distances, cross_times)
            )
        )
        if phash_ok and time_ok and (strict_links >= 2):
            candidates.append(
                {
                    "Group A": group_a,
                    "Group B": group_b,
                    "Members A": len(members_a),
                    "Members B": len(members_b),
                    "Strict Cross Links": int(strict_links),
                    "Max Cross pHash": max(cross_distances),
                    "Max Cross Time Seconds": max(cross_times),
                }
            )
    counts = {}
    for item in candidates:
        for g in (item["Group A"], item["Group B"]):
            counts[g] = counts.get(g, 0) + 1
    accepted = []
    for item in candidates:
        a, b = (item["Group A"], item["Group B"])
        if counts[a] != 1 or counts[b] != 1:
            continue
        first_a, first_b = (min(original_groups[a]), min(original_groups[b]))
        keep, absorb = (a, b) if first_a <= first_b else (b, a)
        result.loc[result["similarityGroup"].eq(absorb), "similarityGroup"] = keep
        accepted.append({**item, "Merged Group": keep, "Absorbed Group": absorb})
    return (result, pd.DataFrame(accepted))


def apply_group_merge_safety_guard(results, before_group_merge, merge_log, params):
    """No deletion recommendation may depend solely on a relaxed group merge.

    Previously separate best shots are protected if they lose their best-shot
    status. Other new deletion recommendations require a strict EXIF+pHash
    match to the new best shot AND must already have been deletion candidates
    inside their own original group. Nothing is physically deleted.
    """
    if merge_log.empty:
        return results
    out = results.copy().reset_index(drop=True)
    old = add_best_shot_and_recommendation(before_group_merge, params).reset_index(
        drop=True
    )
    threshold = int(params["similarity"]["phash_threshold"])
    window = float(params["similarity"]["exif_time_window_seconds"])
    hashes = {
        idx: imagehash.hex_to_hash(str(row["phash"]))
        for idx, row in out.iterrows()
        if pd.notna(row.get("phash"))
    }

    def mark_review(idx, message):
        out.at[idx, "recommendation"] = "REVIEW"
        reasons = out.at[idx, "reasons"]
        if not isinstance(reasons, list):
            reasons = [str(reasons)]
        if message not in reasons:
            out.at[idx, "reasons"] = reasons + [message]

    for merged_group in merge_log["Merged Group"].unique():
        member_ids = out.index[out["similarityGroup"].eq(merged_group)].tolist()
        best_ids = [i for i in member_ids if bool(out.at[i, "bestShot"])]
        ambiguous = len(best_ids) != 1 or any(
            (bool(out.at[i, "bestShotNeedsReview"]) for i in member_ids)
        )
        best_idx = best_ids[0] if len(best_ids) == 1 else None
        for idx in member_ids:
            if ambiguous:
                if out.at[idx, "recommendation"] in ("KEEP", "RECOMMEND_DELETE"):
                    mark_review(idx, "Merged groups require manual verification")
                continue
            if bool(old.at[idx, "bestShot"]) and idx != best_idx:
                mark_review(
                    idx, "Previously best in a separate group: review before deletion"
                )
                continue
            if out.at[idx, "recommendation"] != "RECOMMEND_DELETE":
                continue
            delta = _time_difference_seconds(
                out.at[idx, "taken_at"], out.at[best_idx, "taken_at"]
            )
            strict_to_best = (
                idx in hashes
                and best_idx in hashes
                and (delta is not None)
                and (delta <= window)
                and (int(hashes[idx] - hashes[best_idx]) <= threshold)
            )
            if (
                old.at[idx, "recommendation"] != "RECOMMEND_DELETE"
                or not strict_to_best
            ):
                mark_review(idx, "Group merge uncertain: verify before deletion")
    return out


def apply_rescue_safety_guard(results, before_rescue, rescue_log, params):
    """Review uncertain rescue matches, without penalizing verified original members.

    A rescued image is always REVIEW unless a separate review confirms it.
    Original group members may retain their normal deletion recommendation only
    if two other *original* members independently pass strict EXIF + pHash.
    No image is deleted by this function; it only changes recommendation labels.
    """
    if rescue_log.empty:
        return results
    output = results.copy()
    cfg = params["similarity"]
    phash_threshold = int(cfg["phash_threshold"])
    time_window = float(cfg["exif_time_window_seconds"])
    originals = before_rescue.reset_index(drop=True)
    output = output.reset_index(drop=True)
    rescued_mask = (
        originals["similarityGroup"].isna() & output["similarityGroup"].notna()
    )
    affected = output.loc[rescued_mask, "similarityGroup"].unique()
    hash_cache = {
        idx: imagehash.hex_to_hash(str(row["phash"]))
        for idx, row in output.iterrows()
        if pd.notna(row.get("phash"))
    }

    def strict_match(left, right):
        if left not in hash_cache or right not in hash_cache:
            return False
        dt = _time_difference_seconds(
            output.at[left, "taken_at"], output.at[right, "taken_at"]
        )
        return bool(
            dt is not None
            and dt <= time_window
            and (hash_cache[left] - hash_cache[right] <= phash_threshold)
        )

    def require_review(idx, note):
        output.at[idx, "recommendation"] = "REVIEW"
        reasons = output.at[idx, "reasons"]
        if not isinstance(reasons, list):
            reasons = [str(reasons)]
        if note not in reasons:
            output.at[idx, "reasons"] = reasons + [note]

    for group_id in affected:
        all_ids = output.index[output["similarityGroup"].eq(group_id)].tolist()
        original_ids = [idx for idx in all_ids if not bool(rescued_mask.iloc[idx])]
        rescued_ids = [idx for idx in all_ids if bool(rescued_mask.iloc[idx])]
        best_ids = [idx for idx in all_ids if bool(output.at[idx, "bestShot"])]
        ambiguous_group = (
            len(rescued_ids) != 1
            or len(best_ids) != 1
            or best_ids[0] not in original_ids
            or any((bool(output.at[idx, "bestShotNeedsReview"]) for idx in all_ids))
        )
        best_idx = best_ids[0] if len(best_ids) == 1 else None
        for idx in all_ids:
            rec = output.at[idx, "recommendation"]
            if bool(rescued_mask.iloc[idx]):
                require_review(idx, "Rescued similarity match: confirm group manually")
                continue
            if ambiguous_group:
                if rec in ("RECOMMEND_DELETE", "KEEP"):
                    require_review(
                        idx, "Uncertain rescued group: manual review required"
                    )
                continue
            if rec != "RECOMMEND_DELETE":
                continue
            other_originals = [j for j in original_ids if j != idx]
            confirmations = sum((strict_match(idx, j) for j in other_originals))
            safely_matched = strict_match(idx, best_idx) and confirmations >= 2
            if not safely_matched:
                require_review(idx, "Insufficient original-group similarity evidence")
    return output


def run_core_pipeline(
    features,
    params,
    missing_exif_policy=None,
    use_rescue=True,
    use_group_merge=None,
):
    scored = add_quality_scores(features, params)
    grouped, similarity_pairs = build_similarity_groups(
        scored, params, missing_exif_policy=missing_exif_policy
    )
    if params["similarity"]["strategy"] == "exif_time_or_phash":
        # Notebook rescue/merge and their guards depend on pHash for timed photos.
        # This mode uses its own time-first / timed-pHash grouping rules.
        return add_best_shot_and_recommendation(grouped, params), similarity_pairs
    before_rescue = grouped.copy()
    rescue_log = pd.DataFrame()
    if use_rescue:
        grouped, rescue_log = rescue_borderline_singletons(grouped, params)
    if use_group_merge is None:
        use_group_merge = use_rescue
    before_group_merge = grouped.copy()
    merge_log = pd.DataFrame()
    if use_group_merge:
        grouped, merge_log = merge_nearby_similarity_groups(
            grouped, params, rescue_log=rescue_log
        )
    results = add_best_shot_and_recommendation(grouped, params)
    if use_rescue and (not rescue_log.empty):
        results = apply_rescue_safety_guard(results, before_rescue, rescue_log, params)
    if use_group_merge and (not merge_log.empty):
        results = apply_group_merge_safety_guard(
            results, before_group_merge, merge_log, params
        )
    return (results, similarity_pairs)


def run_pipeline(
    image_paths: list[Path],
    params: dict[str, Any],
    *,
    use_rescue: bool = True,
    use_group_merge: bool | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = pd.DataFrame([extract_features(path) for path in image_paths])
    return analyze_features(
        features, params, use_rescue=use_rescue, use_group_merge=use_group_merge
    )


def analyze_features(
    features_df: pd.DataFrame,
    params: dict[str, Any],
    *,
    use_rescue: bool = True,
    use_group_merge: bool | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if features_df.empty:
        return features_df.copy(), pd.DataFrame()
    return run_core_pipeline(
        features_df,
        params,
        use_rescue=use_rescue,
        use_group_merge=use_group_merge,
    )
