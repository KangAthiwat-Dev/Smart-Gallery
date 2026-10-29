import copy
import io
import unittest

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.parameters import load_parameters, validate_parameters
from app.services.pipeline import (
    add_best_shot_and_recommendation,
    add_quality_scores,
    build_similarity_groups,
    classify_exposure,
    classify_sharpness,
)
from fixtures import BASE_PARAMETERS


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.params = copy.deepcopy(BASE_PARAMETERS)

    def test_sharpness_threshold_and_normalized_score(self):
        threshold = self.params["sharpness"]["threshold"]
        row = pd.Series(
            {
                "laplacian_score": threshold,
                "brightness_mean": 100,
                "dark_clipping_ratio": 0,
                "highlight_clipping_ratio": 0,
            }
        )
        self.assertEqual(classify_sharpness(row, self.params), "sharp")
        result = add_quality_scores(pd.DataFrame([row]), self.params).iloc[0]
        self.assertAlmostEqual(result["sharpnessScore"], 50)
        self.assertAlmostEqual(result["exposureScore"], 100)
        self.assertAlmostEqual(result["qualityScore"], 70)

    def test_exposure_boundaries_and_underexposure_precedence(self):
        row = pd.Series(
            {
                "brightness_mean": 80.0,
                "dark_clipping_ratio": 0.0,
                "highlight_clipping_ratio": 0.0,
            }
        )
        self.assertEqual(classify_exposure(row, self.params), "underexposed")
        row["brightness_mean"] = 145
        self.assertEqual(classify_exposure(row, self.params), "overexposed")
        row["dark_clipping_ratio"] = 0.15
        row["highlight_clipping_ratio"] = 0.03
        self.assertEqual(classify_exposure(row, self.params), "underexposed")

    def test_strict_missing_exif_and_time_window(self):
        rows = [
            {"filename": str(i), "phash": "0000000000000000", "taken_at": time}
            for i, time in enumerate(
                [None, "2026-10-23T12:00:00", "2026-10-23T12:00:21"]
            )
        ]
        result, _ = build_similarity_groups(pd.DataFrame(rows), self.params)
        self.assertTrue(result["similarityGroup"].isna().all())
        rows[2]["taken_at"] = "2026-10-23T12:00:20"
        result, _ = build_similarity_groups(pd.DataFrame(rows), self.params)
        self.assertTrue(pd.isna(result.iloc[0]["similarityGroup"]))
        self.assertEqual(
            result.iloc[1]["similarityGroup"], result.iloc[2]["similarityGroup"]
        )

    def test_complete_link_does_not_merge_a_chain(self):
        self.params["similarity"]["phash_threshold"] = 1
        rows = [
            {"filename": str(i), "phash": value, "taken_at": "2026-10-23T12:00:00"}
            for i, value in enumerate(
                ["0000000000000000", "0000000000000001", "0000000000000003"]
            )
        ]
        result, pairs = build_similarity_groups(pd.DataFrame(rows), self.params)
        self.assertEqual(result["similarityGroup"].notna().sum(), 2)
        self.assertEqual(pairs["is_similar"].sum(), 2)

    def test_best_shot_gap_boundary_and_singletons(self):
        rows = [
            {
                "similarityGroup": group,
                "qualityScore": quality,
                "sharpness_label": sharp,
                "exposure_label_pred": exposure,
            }
            for group, quality, sharp, exposure in [
                ("G001", 80, "sharp", "normal"),
                ("G001", 75, "sharp", "normal"),
                ("G001", 76, "sharp", "normal"),
                (None, 40, "blur", "normal"),
                (None, 80, "sharp", "normal"),
            ]
        ]
        result = add_best_shot_and_recommendation(pd.DataFrame(rows), self.params)
        self.assertEqual(
            list(result["recommendation"]),
            ["KEEP", "RECOMMEND_DELETE", "REVIEW", "REVIEW", "KEEP"],
        )
        self.assertEqual(list(result["bestShot"]), [True, False, False, False, False])

    def test_bad_parameters_are_rejected(self):
        for section, key, value in [
            ("similarity", "strategy", "phash_only"),
            ("similarity", "strategy", "exif_phash_ssim"),
            ("similarity", "ssim_threshold", 0.85),
            ("similarity", "linkage", "single"),
            ("similarity", "missing_exif_policy", "unknown"),
            ("similarity", "phash_threshold", 65),
            ("recommendation", "best_shot_tie_margin", -1),
            ("quality_score", "sharpness_weight", 0.8),
            ("sharpness", "threshold", float("nan")),
        ]:
            params = copy.deepcopy(self.params)
            params[section][key] = value
            with self.assertRaises(ValueError):
                validate_parameters(params)

    def test_loading_defaults_does_not_overwrite_the_parameter_file(self):
        import json
        import tempfile
        from pathlib import Path

        params = copy.deepcopy(BASE_PARAMETERS)
        params["similarity"].pop("linkage")
        params["recommendation"].pop("best_shot_tie_margin")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best_parameters.json"
            path.write_text(json.dumps(params))
            before = path.read_bytes()
            loaded = load_parameters(path)
            self.assertEqual(loaded["similarity"]["linkage"], "complete")
            self.assertEqual(loaded["similarity"]["missing_exif_policy"], "strict")
            self.assertEqual(loaded["recommendation"]["best_shot_tie_margin"], 2.0)
            self.assertEqual(path.read_bytes(), before)

    def test_latest_parameters_are_accepted_without_a_ssim_key(self):
        from fixtures import latest_parameters

        params = latest_parameters()
        self.assertIs(validate_parameters(params), params)
        self.assertEqual(params["similarity"]["linkage"], "average")


def jpeg_bytes(orientation=None, timestamp=None):
    image = Image.fromarray(
        np.random.default_rng(7).integers(0, 255, (80, 120, 3), dtype=np.uint8)
    )
    exif = Image.Exif()
    if orientation:
        exif[274] = orientation
    if timestamp:
        exif[34665] = {36867: timestamp}
    output = io.BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


class ApiTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch

        patcher = patch("app.main.PARAMS", copy.deepcopy(BASE_PARAMETERS))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(app)

    def analyze(self, files, entries):
        import json

        return self.client.post(
            "/analyze", files=files, data={"manifest": json.dumps(entries)}
        )

    def test_exposure_display_metrics_distinguish_identical_full_scores(self):
        normal = Image.new("RGB", (100, 100), (100, 100, 100))
        boundary = Image.new("RGB", (100, 100), (145, 145, 145))
        highlights = normal.copy()
        highlights.paste((255, 255, 255), (0, 0, 3, 100))
        files = []
        for name, image in [
            ("normal", normal),
            ("boundary", boundary),
            ("highlights", highlights),
        ]:
            output = io.BytesIO()
            image.save(output, format="PNG")
            files.append(("files", (f"{name}.png", output.getvalue(), "image/png")))
        response = self.analyze(
            files,
            [
                {"id": name, "relativePath": f"{name}.png"}
                for name in ("normal", "boundary", "highlights")
            ],
        )
        self.assertEqual(response.status_code, 200, response.text)
        photos = response.json()["photos"]
        self.assertEqual([p["exposureScore"] for p in photos], [100, 100, 100])
        self.assertEqual(
            [p["exposureLabel"] for p in photos],
            ["normal", "overexposed", "overexposed"],
        )
        self.assertEqual(photos[0]["exposureMetrics"]["brightnessMean"], 100)
        self.assertEqual(photos[1]["exposureMetrics"]["brightnessMean"], 145)
        self.assertLess(photos[2]["exposureMetrics"]["brightnessMean"], 145)
        self.assertEqual(photos[2]["exposureMetrics"]["highlightClippingRatio"], 0.03)

    def test_partial_failure_ids_duplicate_filenames_and_jpeg_preview(self):
        response = self.analyze(
            [
                ("files", ("same.jpg", jpeg_bytes(), "image/jpeg")),
                ("files", ("broken.jpg", b"not an image", "image/jpeg")),
                ("files", ("same.jpg", jpeg_bytes(6), "image/jpeg")),
            ],
            [
                {"id": "first", "relativePath": "one/same.jpg"},
                {"id": "bad", "relativePath": "broken.jpg"},
                {"id": "last", "relativePath": "two/same.jpg"},
            ],
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual([p["id"] for p in data["photos"]], ["first", "last"])
        self.assertEqual(
            [p["filename"] for p in data["photos"]], ["same.jpg", "same.jpg"]
        )
        self.assertEqual(data["issues"][0]["id"], "bad")
        self.assertEqual(data["summary"]["missingExifCount"], 2)
        self.assertTrue(all(p["similarityGroup"] is None for p in data["photos"]))
        self.assertTrue(
            data["photos"][0]["imageUrl"].startswith("data:image/jpeg;base64,")
        )
        self.assertEqual(
            (data["photos"][1]["width"], data["photos"][1]["height"]), (80, 120)
        )
        self.assertEqual(data["parameters"]["similarity"]["strategy"], "exif_phash")
        self.assertTrue(
            all(isinstance(p["bestShotNeedsReview"], bool) for p in data["photos"])
        )

    def test_all_corrupt_returns_actionable_error(self):
        response = self.analyze(
            [("files", ("broken.jpg", b"broken", "image/jpeg"))],
            [{"id": "broken", "relativePath": "broken.jpg"}],
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["issues"][0]["id"], "broken")

    def test_latest_api_exposes_average_linkage_and_near_tied_best_shot_review(self):
        from unittest.mock import patch
        from fixtures import latest_parameters

        with patch("app.main.PARAMS", latest_parameters()):
            image = jpeg_bytes(timestamp="2026:10:29 12:00:00")
            response = self.analyze(
                [
                    ("files", ("first.jpg", image, "image/jpeg")),
                    ("files", ("second.jpg", image, "image/jpeg")),
                ],
                [
                    {"id": "first", "relativePath": "first.jpg"},
                    {"id": "second", "relativePath": "second.jpg"},
                ],
            )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["parameters"]["similarity"]["linkage"], "average")
        self.assertEqual(
            data["parameters"]["recommendation"]["best_shot_tie_margin"], 0.25
        )
        self.assertEqual(data["summary"]["keepCount"], 0)
        self.assertEqual(data["summary"]["reviewCount"], 2)
        self.assertEqual(data["summary"]["recommendDeleteCount"], 0)
        self.assertEqual(sum(p["bestShot"] for p in data["photos"]), 1)
        self.assertTrue(all(p["bestShotNeedsReview"] for p in data["photos"]))

    def test_nested_exif_and_missing_timestamp_in_same_batch(self):
        response = self.analyze(
            [
                (
                    "files",
                    (
                        "camera.jpg",
                        jpeg_bytes(timestamp="2026:10:23 12:00:00"),
                        "image/jpeg",
                    ),
                ),
                ("files", ("export.jpg", jpeg_bytes(), "image/jpeg")),
            ],
            [
                {"id": "camera", "relativePath": "camera.jpg"},
                {"id": "export", "relativePath": "export.jpg"},
            ],
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["photos"][0]["takenAt"], "2026-10-23T12:00:00")
        self.assertIsNone(data["photos"][1]["takenAt"])
        self.assertEqual(data["summary"]["missingExifCount"], 1)

    def test_duplicate_manifest_ids_rejected(self):
        response = self.analyze(
            [("files", ("one.jpg", jpeg_bytes(), "image/jpeg"))] * 2,
            [{"id": "same", "relativePath": "one.jpg"}] * 2,
        )
        self.assertEqual(response.status_code, 400)

    def test_file_size_is_checked_on_server(self):
        from unittest.mock import patch

        with patch("app.main.MAX_FILE_BYTES", 16):
            response = self.analyze(
                [("files", ("one.jpg", jpeg_bytes(), "image/jpeg"))],
                [{"id": "one", "relativePath": "one.jpg"}],
            )
        self.assertEqual(response.status_code, 413)

    def test_heic_becomes_browser_compatible_preview(self):
        import pillow_heif

        output = io.BytesIO()
        pillow_heif.from_pillow(Image.new("RGB", (64, 48), (100, 120, 140))).save(
            output
        )
        response = self.analyze(
            [("files", ("phone.heic", output.getvalue(), "image/heic"))],
            [{"id": "phone", "relativePath": "phone.heic"}],
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(
            response.json()["photos"][0]["imageUrl"].startswith(
                "data:image/jpeg;base64,"
            )
        )


if __name__ == "__main__":
    unittest.main()
