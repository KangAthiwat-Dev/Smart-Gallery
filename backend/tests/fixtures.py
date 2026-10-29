"""Test parameters are independent of the user's editable runtime JSON."""

from copy import deepcopy

BASE_PARAMETERS = {
    "sharpness": {"method": "laplacian_score", "threshold": 574.4107330939421},
    "exposure": {
        "low_brightness": 80.0,
        "high_brightness": 145.0,
        "dark_clip_threshold": 0.15,
        "highlight_clip_threshold": 0.03,
    },
    "similarity": {
        "strategy": "exif_phash",
        "phash_threshold": 34,
        "exif_time_window_seconds": 20,
        "linkage": "complete",
    },
    "quality_score": {"sharpness_weight": 0.6, "exposure_weight": 0.4},
    "recommendation": {"duplicate_quality_gap": 5.0, "best_shot_tie_margin": 2.0},
}


def latest_parameters():
    params = deepcopy(BASE_PARAMETERS)
    params["similarity"].update(
        phash_threshold=29, exif_time_window_seconds=30, linkage="average"
    )
    params["quality_score"].update(sharpness_weight=0.2, exposure_weight=0.8)
    params["recommendation"]["best_shot_tie_margin"] = 0.25
    return params
