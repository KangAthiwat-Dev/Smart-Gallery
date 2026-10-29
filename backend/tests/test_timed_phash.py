"""Time groups stay intact; a separate pHash threshold can join them later."""

import json
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.parameters import validate_parameters
from app.services.pipeline import run_core_pipeline
from test_latest_algorithm import rows
from test_pipeline import jpeg_bytes
from test_time_or_phash import parameters


class TimedPhashTests(unittest.TestCase):
    def setUp(self):
        self.params = parameters()
        self.params["similarity"]["timed_phash_threshold"] = 2

    def test_out_of_window_photos_match_at_the_separate_threshold_boundary(self):
        features = rows([0, 3], times=[0, 40])
        features.loc[1, "laplacian_score"] = 10
        result, pairs = run_core_pipeline(features, self.params)
        self.assertTrue(result["similarityGroup"].notna().all())
        self.assertEqual(result["similarityGroup"].nunique(), 1)
        self.assertTrue(result["timedPhashMatch"].all())
        self.assertEqual(
            result["recommendation"].tolist(), ["KEEP", "RECOMMEND_DELETE"]
        )
        self.assertEqual(pairs.iloc[0]["strategy"], "timed_phash")
        self.assertEqual(pairs.iloc[0]["hamming_distance"], 2)
        self.assertTrue(pairs.iloc[0]["is_similar"])
        self.assertIn(
            "Capture-time groups combined using the timed pHash threshold.",
            result.loc[0, "reasons"],
        )
        self.assertNotIn(
            "Capture-time grouping only; pHash was not used.", result.loc[0, "reasons"]
        )
        self.params["similarity"]["timed_phash_threshold"] = 1
        result, pairs = run_core_pipeline(features, self.params)
        self.assertTrue(result["similarityGroup"].isna().all())
        self.assertFalse(pairs.iloc[0]["is_similar"])

    def test_within_window_photos_never_have_to_pass_phash(self):
        features = rows([0, (1 << 64) - 1], times=[0, 30])
        features["phash"] = None
        self.params["similarity"]["timed_phash_threshold"] = 0
        with patch(
            "app.services.pipeline.imagehash.hex_to_hash",
            side_effect=AssertionError("A time match must not depend on pHash"),
        ):
            result, pairs = run_core_pipeline(features, self.params)
        self.assertEqual(result["similarityGroup"].nunique(), 1)
        self.assertTrue(result["similarityGroup"].notna().all())
        self.assertFalse(result["timedPhashMatch"].any())
        self.assertEqual(pairs.iloc[0]["strategy"], "exif_time")

    def test_timed_and_untimed_thresholds_are_independent_and_never_mix(self):
        features = rows([0, 3, 0, 3], times=[0, 40, 0, 0])
        features.loc[[2, 3], "taken_at"] = None
        result, _ = run_core_pipeline(features, self.params)
        self.assertTrue(result.loc[[0, 1], "similarityGroup"].notna().all())
        self.assertTrue(result.loc[[2, 3], "similarityGroup"].isna().all())
        self.params["similarity"].update(phash_threshold=2, timed_phash_threshold=1)
        result, _ = run_core_pipeline(features, self.params)
        self.assertTrue(result.loc[[0, 1], "similarityGroup"].isna().all())
        self.assertTrue(result.loc[[2, 3], "similarityGroup"].notna().all())
        self.params["similarity"]["timed_phash_threshold"] = 2
        result, _ = run_core_pipeline(features, self.params)
        self.assertEqual(result["similarityGroup"].nunique(), 2)
        self.assertNotEqual(
            result.loc[0, "similarityGroup"], result.loc[2, "similarityGroup"]
        )
        self.assertFalse(result.loc[[2, 3], "timedPhashMatch"].any())

    def test_existing_time_group_is_never_split_to_take_a_partial_phash_match(self):
        features = rows([0, (1 << 64) - 1, 0], times=[0, 1, 40])
        result, pairs = run_core_pipeline(features, self.params)
        self.assertEqual(
            result.loc[0, "similarityGroup"], result.loc[1, "similarityGroup"]
        )
        self.assertTrue(pd.notna(result.loc[0, "similarityGroup"]))
        self.assertTrue(pd.isna(result.loc[2, "similarityGroup"]))
        self.assertFalse(result["timedPhashMatch"].any())
        self.assertTrue(
            pairs.iloc[1]["is_similar"]
        )  # One link alone cannot pull a group.

    def test_whole_time_groups_can_merge_with_all_cross_pairs_confirmed(self):
        self.params["similarity"]["timed_phash_threshold"] = 3
        features = rows([0, 1, 3, 7], times=[0, 1, 40, 41])
        result, _ = run_core_pipeline(features, self.params)
        self.assertTrue(result["similarityGroup"].notna().all())
        self.assertEqual(result["similarityGroup"].nunique(), 1)
        self.assertTrue(result["timedPhashMatch"].all())

    def test_similar_chain_cannot_pull_in_an_incompatible_timed_photo(self):
        features = rows([0, 3, 15])
        features["taken_at"] = [
            "2026-10-29T12:00:00",
            "2026-10-29T12:01:00",
            "2026-10-29T12:02:00",
        ]
        result, _ = run_core_pipeline(features, self.params)
        self.assertEqual(result["similarityGroup"].notna().sum(), 2)
        self.assertEqual(result["similarityGroup"].nunique(), 1)

    def test_omitted_or_null_timed_threshold_keeps_time_only_behavior(self):
        for threshold in (None, "omitted"):
            with self.subTest(threshold=threshold):
                if threshold == "omitted":
                    self.params["similarity"].pop("timed_phash_threshold")
                else:
                    self.params["similarity"]["timed_phash_threshold"] = threshold
                result, _ = run_core_pipeline(rows([0, 0], times=[0, 40]), self.params)
                self.assertTrue(result["similarityGroup"].isna().all())

    def test_timed_threshold_validation(self):
        for threshold in (0, 29, 64, None):
            self.params["similarity"]["timed_phash_threshold"] = threshold
            self.assertIs(validate_parameters(self.params), self.params)
        for threshold in (-1, 65, 2.5, True, "29", float("nan")):
            with self.subTest(threshold=threshold):
                self.params["similarity"]["timed_phash_threshold"] = threshold
                with self.assertRaises(ValueError):
                    validate_parameters(self.params)


class TimedPhashApiTests(unittest.TestCase):
    def test_upload_exposes_the_new_threshold_and_explains_a_beyond_window_match(self):
        params = parameters()
        params["similarity"]["timed_phash_threshold"] = 29
        uploads = [
            ("camera-a", jpeg_bytes(timestamp="2026:10:29 12:00:00")),
            ("camera-b", jpeg_bytes(timestamp="2026:10:29 12:00:40")),
            ("export", jpeg_bytes()),
        ]
        with patch("app.main.PARAMS", params):
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
        self.assertEqual(health["timedPhashThreshold"], 29)
        self.assertEqual(data["parameters"]["similarity"]["timed_phash_threshold"], 29)
        self.assertTrue(photos["camera-a"]["similarityGroup"])
        self.assertEqual(
            photos["camera-a"]["similarityGroup"], photos["camera-b"]["similarityGroup"]
        )
        self.assertIsNone(photos["export"]["similarityGroup"])
        self.assertIn(
            "Capture-time groups combined using the timed pHash threshold.",
            photos["camera-a"]["reasons"],
        )


if __name__ == "__main__":
    unittest.main()
