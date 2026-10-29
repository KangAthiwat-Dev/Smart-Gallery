"""The demo's capture-time-only / untimed-pHash grouping rules."""

import io
import json
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.parameters import validate_parameters
from app.services.pipeline import build_similarity_groups, run_core_pipeline
from fixtures import latest_parameters
from test_latest_algorithm import rows
from test_pipeline import jpeg_bytes


def parameters():
    params = latest_parameters()
    params["similarity"].update(
        strategy="exif_time_or_phash", missing_exif_policy="phash", phash_threshold=0
    )
    return params


class TimeOrPhashTests(unittest.TestCase):
    def setUp(self):
        self.params = parameters()

    def test_timed_photos_group_without_reading_phash_at_any_threshold(self):
        features = rows([0, (1 << 64) - 1], times=[0, 30])
        features["phash"] = None
        for linkage in ("complete", "average"):
            for threshold in (0, 10, 64):
                with self.subTest(linkage=linkage, threshold=threshold):
                    self.params["similarity"].update(
                        linkage=linkage, phash_threshold=threshold
                    )
                    with patch(
                        "app.services.pipeline.imagehash.hex_to_hash",
                        side_effect=AssertionError(
                            "Timed grouping must not read pHash"
                        ),
                    ):
                        result, pairs = run_core_pipeline(features, self.params)
                    self.assertTrue(result["similarityGroup"].notna().all())
                    self.assertEqual(result["similarityGroup"].nunique(), 1)
                    self.assertEqual(pairs.iloc[0]["strategy"], "exif_time")
                    self.assertEqual(pairs.iloc[0]["time_difference_seconds"], 30)
                    self.assertTrue(pd.isna(pairs.iloc[0]["hamming_distance"]))
                    self.assertTrue(pairs.iloc[0]["is_similar"])
                    self.assertTrue(
                        all(
                            "Capture-time grouping only; pHash was not used." in reasons
                            for reasons in result["reasons"]
                        )
                    )

    def test_identical_photos_outside_the_time_window_do_not_group(self):
        result, pairs = run_core_pipeline(rows([0, 0], times=[0, 31]), self.params)
        self.assertTrue(result["similarityGroup"].isna().all())
        self.assertFalse(pairs.iloc[0]["is_similar"])

    def test_zero_time_window_groups_only_identical_timestamps(self):
        self.params["similarity"]["exif_time_window_seconds"] = 0
        result, _ = run_core_pipeline(rows([0, 1, 3], times=[0, 0, 1]), self.params)
        self.assertEqual(result["similarityGroup"].notna().sum(), 2)
        self.assertEqual(
            result.loc[0, "similarityGroup"], result.loc[1, "similarityGroup"]
        )
        self.assertTrue(pd.isna(result.loc[2, "similarityGroup"]))

    def test_timed_groups_cannot_expand_beyond_the_window_through_a_chain(self):
        features = rows([0, 0, 0], times=[0, 20, 40])
        result, _ = run_core_pipeline(features, self.params)
        self.assertEqual(result["similarityGroup"].notna().sum(), 2)
        for _, group in result.dropna(subset=["similarityGroup"]).groupby(
            "similarityGroup"
        ):
            timestamps = pd.to_datetime(group["taken_at"])
            self.assertLessEqual(
                (timestamps.max() - timestamps.min()).total_seconds(), 30
            )

    def test_only_untimed_photos_respond_to_phash_threshold(self):
        features = rows([0, 0, (1 << 64) - 1, 3], times=[0, 0, 0, 0])
        features.loc[[1, 3], "taken_at"] = None
        low, _ = run_core_pipeline(features, self.params)
        self.assertTrue(low.loc[[0, 2], "similarityGroup"].notna().all())
        self.assertTrue(low.loc[[1, 3], "similarityGroup"].isna().all())
        self.params["similarity"]["phash_threshold"] = 2
        high, _ = run_core_pipeline(features, self.params)
        self.assertTrue(high["similarityGroup"].notna().all())
        self.assertEqual(high.loc[0, "similarityGroup"], high.loc[2, "similarityGroup"])
        self.assertEqual(high.loc[1, "similarityGroup"], high.loc[3, "similarityGroup"])
        self.assertNotEqual(
            high.loc[0, "similarityGroup"], high.loc[1, "similarityGroup"]
        )

    def test_strict_missing_policy_excludes_untimed_photos_without_affecting_timed(
        self,
    ):
        self.params["similarity"]["missing_exif_policy"] = "strict"
        features = rows([0, 0, 0, 0])
        features.loc[[1, 3], "taken_at"] = [None, "invalid timestamp"]
        result, _ = run_core_pipeline(features, self.params)
        self.assertTrue(result.loc[[0, 2], "similarityGroup"].notna().all())
        self.assertTrue(result.loc[[1, 3], "similarityGroup"].isna().all())

    def test_time_only_quality_recommendations_do_not_depend_on_legacy_refinements(
        self,
    ):
        features = rows([0, (1 << 64) - 1], times=[0, 1])
        features.loc[1, "laplacian_score"] = 10
        with (
            patch("app.services.pipeline.rescue_borderline_singletons") as rescue,
            patch("app.services.pipeline.merge_nearby_similarity_groups") as merge,
        ):
            result, _ = run_core_pipeline(features, self.params)
        rescue.assert_not_called()
        merge.assert_not_called()
        self.assertEqual(
            result["recommendation"].tolist(), ["KEEP", "RECOMMEND_DELETE"]
        )
        self.assertIn("Best shot in a capture-time group", result.loc[0, "reasons"])
        self.assertIn(
            "Photo in the same capture-time group has a higher quality score",
            result.loc[1, "reasons"],
        )

    def test_new_strategy_is_validated(self):
        self.assertIs(validate_parameters(self.params), self.params)


class TimeOrPhashApiTests(unittest.TestCase):
    def test_real_uploads_use_time_for_different_camera_images_and_phash_for_exports(
        self,
    ):
        exif = Image.Exif()
        exif[34665] = {36867: "2026:10:29 12:00:01"}
        output = io.BytesIO()
        Image.new("RGB", (120, 80), (100, 100, 100)).save(
            output, format="JPEG", exif=exif
        )
        uploads = [
            ("camera-a", jpeg_bytes(timestamp="2026:10:29 12:00:00")),
            ("export-a", jpeg_bytes()),
            ("camera-b", output.getvalue()),
            ("export-b", jpeg_bytes()),
        ]
        with patch("app.main.PARAMS", parameters()):
            client = TestClient(app)
            health = client.get("/health").json()
            response = client.post(
                "/analyze",
                files=[
                    ("files", (f"{name}.jpg", content, "image/jpeg"))
                    for name, content in uploads
                ],
                data={
                    "manifest": json.dumps(
                        [
                            {"id": name, "relativePath": f"{name}.jpg"}
                            for name, _ in uploads
                        ]
                    )
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        photos = {photo["id"]: photo for photo in data["photos"]}
        self.assertEqual(health["similarityStrategy"], "exif_time_or_phash")
        self.assertFalse(health["singletonRescue"])
        self.assertFalse(health["groupMerge"])
        self.assertEqual(
            data["parameters"]["similarity"]["strategy"], "exif_time_or_phash"
        )
        self.assertEqual(data["summary"]["missingExifCount"], 2)
        self.assertTrue(all(photo["similarityGroup"] for photo in photos.values()))
        self.assertEqual(
            photos["camera-a"]["similarityGroup"], photos["camera-b"]["similarityGroup"]
        )
        self.assertEqual(
            photos["export-a"]["similarityGroup"], photos["export-b"]["similarityGroup"]
        )
        self.assertNotEqual(
            photos["camera-a"]["similarityGroup"], photos["export-a"]["similarityGroup"]
        )
        self.assertTrue(photos["camera-a"]["takenAt"])
        self.assertIsNone(photos["export-a"]["takenAt"])
        self.assertIn(
            "Capture-time grouping only; pHash was not used.",
            photos["camera-a"]["reasons"],
        )


if __name__ == "__main__":
    unittest.main()
