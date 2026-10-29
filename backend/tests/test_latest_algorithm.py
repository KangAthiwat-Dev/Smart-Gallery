import unittest

import pandas as pd

from app.services.pipeline import (
    add_best_shot_and_recommendation,
    apply_group_merge_safety_guard,
    apply_rescue_safety_guard,
    build_similarity_groups,
    merge_nearby_similarity_groups,
    rescue_borderline_singletons,
    run_core_pipeline,
)
from fixtures import latest_parameters


def rows(hashes, groups=None, scores=None, times=None):
    size = len(hashes)
    return pd.DataFrame(
        [
            {
                "filename": f"image-{i}.jpg",
                "path": f"/fixture/{i}.jpg",
                "phash": f"{value:016x}",
                "taken_at": (
                    f"2026-10-29T12:00:{times[i]:02d}"
                    if times
                    else "2026-10-29T12:00:00"
                ),
                "similarityGroup": groups[i] if groups else None,
                "qualityScore": float(scores[i]) if scores else 90.0 - i * 10,
                "sharpness_label": "sharp",
                "exposure_label_pred": "normal",
                "laplacian_score": 5000.0 - i * 500,
                "brightness_mean": 100.0,
                "dark_clipping_ratio": 0.0,
                "highlight_clipping_ratio": 0.0,
            }
            for i, value in enumerate(hashes)
        ]
    )


class LatestAlgorithmTests(unittest.TestCase):
    def setUp(self):
        self.params = latest_parameters()

    def test_average_link_uses_raw_distances_instead_of_blocking_high_phash(self):
        features = rows([0, 3, 15])
        self.params["similarity"]["phash_threshold"] = 3
        self.params["similarity"]["linkage"] = "complete"
        complete, _ = build_similarity_groups(features, self.params)
        self.assertEqual(complete["similarityGroup"].notna().sum(), 2)
        self.params["similarity"]["linkage"] = "average"
        average, pairs = build_similarity_groups(features, self.params)
        self.assertEqual(average["similarityGroup"].notna().sum(), 3)
        self.assertEqual(average["similarityGroup"].nunique(), 1)
        self.assertEqual(pairs["is_similar"].sum(), 2)  # One pair exceeds threshold.

    def test_average_link_never_hides_failed_exif_in_the_mean(self):
        features = rows([0, 0, 0], times=[0, 20, 40])
        grouped, _ = build_similarity_groups(features, self.params)
        self.assertEqual(grouped["similarityGroup"].notna().sum(), 2)
        features.loc[1, "taken_at"] = None
        grouped, _ = build_similarity_groups(features, self.params)
        self.assertTrue(grouped["similarityGroup"].isna().all())

    def test_unknown_exif_policy_or_legacy_strategy_is_rejected(self):
        with self.assertRaises(ValueError):
            build_similarity_groups(rows([0, 1]), self.params, "fallback_experimental")
        self.params["similarity"]["strategy"] = "exif_phash_ssim"
        with self.assertRaises(ValueError):
            build_similarity_groups(rows([0, 1]), self.params)

    def test_tie_margin_reviews_only_near_tied_members_in_base_recommendations(self):
        features = rows([0, 0, 0], ["G001"] * 3, [90, 89.8, 70])
        result = add_best_shot_and_recommendation(features, self.params)
        self.assertEqual(
            result["recommendation"].tolist(), ["REVIEW", "REVIEW", "RECOMMEND_DELETE"]
        )
        self.assertEqual(result["bestShotNeedsReview"].tolist(), [True, True, False])
        self.assertEqual(result["bestShot"].sum(), 1)
        # Comparison is strictly less than the margin, not <=.
        features.loc[1, "qualityScore"] = 89.75
        result = add_best_shot_and_recommendation(features, self.params)
        self.assertFalse(result["bestShotNeedsReview"].any())
        self.assertEqual(result.loc[0, "recommendation"], "KEEP")

    def rescue_fixture(self):
        self.params["similarity"]["phash_threshold"] = 3
        return rows([0, 1, 2, 15], ["G001"] * 3 + [None], [90, 70, 60, 50])

    def test_rescued_photo_reviews_but_verified_original_members_keep_delete(self):
        before = self.rescue_fixture()
        grouped, log = rescue_borderline_singletons(before, self.params)
        self.assertEqual(len(log), 1)
        self.assertEqual(grouped.loc[3, "similarityGroup"], "G001")
        result = apply_rescue_safety_guard(
            add_best_shot_and_recommendation(grouped, self.params),
            before,
            log,
            self.params,
        )
        self.assertEqual(
            result["recommendation"].tolist(),
            ["KEEP", "RECOMMEND_DELETE", "RECOMMEND_DELETE", "REVIEW"],
        )
        self.assertIn(
            "Rescued similarity match: confirm group manually", result.loc[3, "reasons"]
        )

    def test_rescued_best_shot_or_multiple_rescues_reviews_entire_group(self):
        before = self.rescue_fixture()
        before.loc[3, "qualityScore"] = 100
        grouped, log = rescue_borderline_singletons(before, self.params)
        result = apply_rescue_safety_guard(
            add_best_shot_and_recommendation(grouped, self.params),
            before,
            log,
            self.params,
        )
        self.assertTrue(result["recommendation"].eq("REVIEW").all())
        before.loc[3, "qualityScore"] = 50
        before = pd.concat(
            [before, before.iloc[[3]].assign(filename="another.jpg")], ignore_index=True
        )
        grouped, log = rescue_borderline_singletons(before, self.params)
        self.assertEqual(len(log), 2)
        result = apply_rescue_safety_guard(
            add_best_shot_and_recommendation(grouped, self.params),
            before,
            log,
            self.params,
        )
        self.assertTrue(result["recommendation"].eq("REVIEW").all())

    def test_rescue_requires_unique_group_three_members_and_valid_time(self):
        before = self.rescue_fixture()
        duplicated_group = before.iloc[:3].copy()
        duplicated_group["similarityGroup"] = "G002"
        candidates = pd.concat([before, duplicated_group], ignore_index=True)
        grouped, log = rescue_borderline_singletons(candidates, self.params)
        self.assertTrue(log.empty)
        self.assertTrue(pd.isna(grouped.loc[3, "similarityGroup"]))
        for excluded in (None, "2026-10-29T12:00:31"):
            candidate = before.copy()
            candidate.loc[3, "taken_at"] = excluded
            _, log = rescue_borderline_singletons(candidate, self.params)
            self.assertTrue(log.empty)
        _, log = rescue_borderline_singletons(before.iloc[[0, 1, 3]], self.params)
        self.assertTrue(log.empty)

    def merge_fixture(self):
        return rows(
            [0] * 5,
            ["G001"] * 3 + ["G002"] * 2,
            [90, 70, 60, 80, 50],
            [0, 10, 20, 40, 50],
        )

    def test_merge_uses_extended_time_but_protects_former_best_and_relaxed_deletes(
        self,
    ):
        before = self.merge_fixture()
        grouped, log = merge_nearby_similarity_groups(before, self.params)
        self.assertEqual(len(log), 1)
        self.assertEqual(grouped["similarityGroup"].nunique(), 1)
        result = apply_group_merge_safety_guard(
            add_best_shot_and_recommendation(grouped, self.params),
            before,
            log,
            self.params,
        )
        self.assertEqual(
            result["recommendation"].tolist(),
            ["KEEP", "RECOMMEND_DELETE", "RECOMMEND_DELETE", "REVIEW", "REVIEW"],
        )
        self.assertIn(
            "Previously best in a separate group: review before deletion",
            result.loc[3, "reasons"],
        )
        self.assertIn(
            "Group merge uncertain: verify before deletion", result.loc[4, "reasons"]
        )

    def test_merge_rejects_ambiguous_targets_rescued_groups_and_excessive_time(self):
        before = self.merge_fixture()
        rescued = pd.DataFrame([{"Assigned Group": "G001"}])
        _, log = merge_nearby_similarity_groups(before, self.params, rescued)
        self.assertTrue(log.empty)
        before.loc[4, "taken_at"] = "2026-10-29T12:01:01"
        _, log = merge_nearby_similarity_groups(before, self.params)
        self.assertTrue(log.empty)
        candidate = pd.concat(
            [self.merge_fixture(), rows([0, 0], ["G003"] * 2, times=[15, 15])],
            ignore_index=True,
        )
        _, log = merge_nearby_similarity_groups(candidate, self.params)
        self.assertTrue(log.empty)

    def test_merged_group_with_near_tied_best_requires_review(self):
        before = self.merge_fixture()
        before.loc[3, "qualityScore"] = 89.8
        grouped, log = merge_nearby_similarity_groups(before, self.params)
        result = apply_group_merge_safety_guard(
            add_best_shot_and_recommendation(grouped, self.params),
            before,
            log,
            self.params,
        )
        self.assertTrue(result["recommendation"].eq("REVIEW").all())

    def test_baseline_toggle_disables_both_refinements(self):
        features = self.rescue_fixture()
        self.params["similarity"]["linkage"] = "complete"
        baseline, _ = run_core_pipeline(features, self.params, use_rescue=False)
        self.assertTrue(pd.isna(baseline.loc[3, "similarityGroup"]))
        rescued, _ = run_core_pipeline(features, self.params, use_group_merge=False)
        self.assertEqual(rescued.loc[3, "similarityGroup"], "G001")
        self.assertEqual(rescued.loc[3, "recommendation"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
