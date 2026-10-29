"""Regression coverage for the optional missing-timestamp pHash fallback."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.pipeline import build_similarity_groups, run_core_pipeline
from fixtures import latest_parameters
from test_latest_algorithm import rows
from test_pipeline import jpeg_bytes


class MissingExifFallbackTests(unittest.TestCase):
    def setUp(self):
        self.params = latest_parameters()
        self.params["similarity"].update(missing_exif_policy="phash", phash_threshold=2)

    def test_similar_photos_group_only_when_both_timestamps_are_missing(self):
        for linkage in ("complete", "average"):
            self.params["similarity"]["linkage"] = linkage
            for timestamps in (
                [None, None],
                [None, "invalid timestamp"],
                ["invalid timestamp", None],
                ["invalid timestamp", "invalid timestamp"],
            ):
                with self.subTest(linkage=linkage, timestamps=timestamps):
                    features = rows([0, 3])  # Distance equals threshold.
                    features["taken_at"] = timestamps
                    grouped, pairs = build_similarity_groups(features, self.params)
                    self.assertTrue(grouped["similarityGroup"].notna().all())
                    self.assertEqual(grouped["similarityGroup"].nunique(), 1)
                    self.assertTrue(pairs.iloc[0]["is_similar"])
                    self.assertEqual(pairs.iloc[0]["strategy"], "phash")

    def test_identical_timed_and_untimed_photos_never_group_together(self):
        for linkage in ("complete", "average"):
            self.params["similarity"]["linkage"] = linkage
            for timestamps in (
                [None, "2026-10-29T12:00:00"],
                ["2026-10-29T12:00:00", None],
                ["invalid timestamp", "2026-10-29T12:00:00"],
                ["2026-10-29T12:00:00", "invalid timestamp"],
            ):
                with self.subTest(linkage=linkage, timestamps=timestamps):
                    features = rows([0, 0])
                    features["taken_at"] = timestamps
                    grouped, pairs = build_similarity_groups(features, self.params)
                    self.assertTrue(grouped["similarityGroup"].isna().all())
                    self.assertFalse(pairs.iloc[0]["is_similar"])

    def test_missing_timestamp_does_not_group_dissimilar_photos(self):
        for linkage in ("complete", "average"):
            with self.subTest(linkage=linkage):
                self.params["similarity"]["linkage"] = linkage
                features = rows([0, 7])  # Distance exceeds threshold.
                features["taken_at"] = None
                grouped, pairs = build_similarity_groups(features, self.params)
                self.assertTrue(grouped["similarityGroup"].isna().all())
                self.assertFalse(pairs.iloc[0]["is_similar"])

    def test_known_timestamps_still_respect_the_original_window(self):
        for seconds, expected in ((30, True), (31, False)):
            with self.subTest(seconds=seconds):
                grouped, pairs = build_similarity_groups(
                    rows([0, 0], times=[0, seconds]), self.params
                )
                self.assertEqual(
                    bool(grouped["similarityGroup"].notna().all()), expected
                )
                self.assertEqual(bool(pairs.iloc[0]["is_similar"]), expected)
                self.assertEqual(pairs.iloc[0]["strategy"], "exif_phash")

    def test_untimed_photo_stays_separate_when_known_timestamps_fail_the_window(self):
        for linkage in ("complete", "average"):
            with self.subTest(linkage=linkage):
                self.params["similarity"]["linkage"] = linkage
                features = rows([0, 0, 0], times=[0, 0, 31])
                features.loc[1, "taken_at"] = None
                grouped, pairs = build_similarity_groups(features, self.params)
                self.assertTrue(grouped["similarityGroup"].isna().all())
                self.assertFalse(pairs["is_similar"].any())

    def test_full_pipeline_keeps_identical_timed_and_untimed_pools_separate(self):
        for linkage in ("complete", "average"):
            with self.subTest(linkage=linkage):
                self.params["similarity"]["linkage"] = linkage
                features = rows([0, 0, 0, 0], times=[0, 1, 2, 3])
                features.loc[[1, 3], "taken_at"] = None
                result, _ = run_core_pipeline(features, self.params)
                self.assertTrue(result["similarityGroup"].notna().all())
                self.assertEqual(result["similarityGroup"].nunique(), 2)
                self.assertEqual(
                    result.loc[0, "similarityGroup"], result.loc[2, "similarityGroup"]
                )
                self.assertEqual(
                    result.loc[1, "similarityGroup"], result.loc[3, "similarityGroup"]
                )
                self.assertNotEqual(
                    result.loc[0, "similarityGroup"], result.loc[1, "similarityGroup"]
                )
                self.assertEqual(result["bestShot"].sum(), 2)

    def test_strict_policy_and_explicit_override_keep_the_notebook_behavior(self):
        features = rows([0, 0])
        features["taken_at"] = None
        strict, _ = build_similarity_groups(features, self.params, "strict")
        self.assertTrue(strict["similarityGroup"].isna().all())
        self.params["similarity"]["missing_exif_policy"] = "strict"
        strict, _ = build_similarity_groups(features, self.params)
        self.assertTrue(strict["similarityGroup"].isna().all())

    def test_full_pipeline_uses_quality_rules_for_fallback_groups(self):
        for linkage in ("complete", "average"):
            with self.subTest(linkage=linkage):
                self.params["similarity"]["linkage"] = linkage
                features = rows([0, 0, (1 << 64) - 1])
                features["taken_at"] = None
                features.loc[1, "laplacian_score"] = 10
                result, _ = run_core_pipeline(features, self.params)
                self.assertEqual(result["similarityGroup"].notna().sum(), 2)
                self.assertEqual(
                    result["recommendation"].tolist(),
                    ["KEEP", "RECOMMEND_DELETE", "KEEP"],
                )
                self.assertEqual(result["bestShot"].tolist(), [True, False, False])


class MissingExifFallbackApiTests(unittest.TestCase):
    def test_api_reports_fallback_policy_group_and_reason_for_missing_timestamps(self):
        import json

        client = TestClient(app)
        for policy in ("strict", "phash"):
            for first_timestamp in (None, "2026:10:29 12:00:00"):
                with self.subTest(policy=policy, first_timestamp=first_timestamp):
                    params = latest_parameters()
                    params["similarity"]["missing_exif_policy"] = policy
                    with patch("app.main.PARAMS", params):
                        health = client.get("/health").json()
                        response = client.post(
                            "/analyze",
                            files=[
                                (
                                    "files",
                                    (
                                        "first.jpg",
                                        jpeg_bytes(timestamp=first_timestamp),
                                        "image/jpeg",
                                    ),
                                ),
                                ("files", ("export.jpg", jpeg_bytes(), "image/jpeg")),
                            ],
                            data={
                                "manifest": json.dumps(
                                    [
                                        {"id": "first", "relativePath": "first.jpg"},
                                        {"id": "export", "relativePath": "export.jpg"},
                                    ]
                                )
                            },
                        )
                    self.assertEqual(response.status_code, 200, response.text)
                    data = response.json()
                    self.assertEqual(health["missingExifPolicy"], policy)
                    self.assertEqual(
                        data["parameters"]["similarity"]["missing_exif_policy"], policy
                    )
                    photos = data["photos"]
                    self.assertEqual(
                        data["summary"]["missingExifCount"],
                        2 if first_timestamp is None else 1,
                    )
                    if policy == "phash" and first_timestamp is None:
                        self.assertTrue(all(p["similarityGroup"] for p in photos))
                        self.assertEqual(
                            photos[0]["similarityGroup"], photos[1]["similarityGroup"]
                        )
                        self.assertEqual(data["summary"]["reviewCount"], 2)
                    else:
                        self.assertTrue(
                            all(p["similarityGroup"] is None for p in photos)
                        )
                    reason = (
                        "Missing EXIF timestamp — pHash comparison is limited to other photos without timestamps."
                        if policy == "phash"
                        else "Missing EXIF timestamp — excluded from similarity grouping (strict EXIF)."
                    )
                    self.assertIn(reason, photos[1]["reasons"])

    def test_api_splits_identical_images_into_timed_and_untimed_groups(self):
        import json

        images = [
            ("camera-a", "2026:10:29 12:00:00"),
            ("export-a", None),
            ("camera-b", "2026:10:29 12:00:01"),
            ("export-b", None),
        ]
        for linkage in ("complete", "average"):
            with self.subTest(linkage=linkage):
                params = latest_parameters()
                params["similarity"].update(
                    missing_exif_policy="phash", linkage=linkage
                )
                with patch("app.main.PARAMS", params):
                    response = TestClient(app).post(
                        "/analyze",
                        files=[
                            (
                                "files",
                                (
                                    f"{name}.jpg",
                                    jpeg_bytes(timestamp=time),
                                    "image/jpeg",
                                ),
                            )
                            for name, time in images
                        ],
                        data={
                            "manifest": json.dumps(
                                [
                                    {"id": name, "relativePath": f"{name}.jpg"}
                                    for name, _ in images
                                ]
                            )
                        },
                    )
                self.assertEqual(response.status_code, 200, response.text)
                data = response.json()
                groups = {p["id"]: p["similarityGroup"] for p in data["photos"]}
                self.assertTrue(all(groups.values()))
                self.assertEqual(groups["camera-a"], groups["camera-b"])
                self.assertEqual(groups["export-a"], groups["export-b"])
                self.assertNotEqual(groups["camera-a"], groups["export-a"])
                self.assertEqual(data["summary"]["missingExifCount"], 2)
                self.assertEqual(sum(p["bestShot"] for p in data["photos"]), 2)


if __name__ == "__main__":
    unittest.main()
