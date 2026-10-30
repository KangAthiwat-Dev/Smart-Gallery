"""The presentation's active functions must keep matching app decisions.

Only named function definitions and simple display constants are loaded.
Drive mounting, installation, prompts and demo cells are never executed here.
"""

import ast
import copy
import hashlib
import inspect
import io
import json
import math
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from PIL import UnidentifiedImageError
from sklearn.metrics import (
    accuracy_score,
    adjusted_rand_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from app import parameters as parameter_module
from app.services import pipeline
from test_latest_algorithm import rows
from test_pipeline import jpeg_bytes
from test_time_or_phash import parameters

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "colab" / "presentation_results.ipynb"
EXTRA_FUNCTIONS = {
    "build_similarity_groups",
    "run_core_pipeline",
    "analyze_features",
    "list_image_files",
    "choose_image_folder",
    "extract_features_batch",
    "analyze_folder",
    "short_reason",
    "summary_table",
    "show_photo_results",
    "export_results",
    "canonical_name",
    "data_source",
    "load_labels",
    "prepare_labeled_features",
    "classification_metrics",
    "normalize_evaluation_labels",
    "classification_outputs",
    "grouping_pair_labels",
    "grouping_metrics",
    "best_shot_metrics",
    "evaluate_current_pipeline",
}
CONSTANTS = {
    "EXPOSURE_TEXT",
    "RECOMMENDATION_TEXT",
    "VALID_DATA_SPLITS",
    "REQUIRED_LABEL_COLUMNS",
    "SHARPNESS_DATASET_TYPES",
    "SHARPNESS_BINARY_MAP",
    "EXPOSURE_CLASSES",
}


def notebook_namespace():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    core_names = set(notebook["metadata"]["smart_gallery"]["app_core_functions"])
    wanted = core_names | EXTRA_FUNCTIONS
    namespace = dict(vars(pipeline))
    namespace.update(
        math=math,
        json=json,
        timezone=timezone,
        accuracy_score=accuracy_score,
        adjusted_rand_score=adjusted_rand_score,
        classification_report=classification_report,
        confusion_matrix=confusion_matrix,
        precision_recall_fscore_support=precision_recall_fscore_support,
        deepcopy=copy.deepcopy,
        display=lambda value: None,
        UnidentifiedImageError=UnidentifiedImageError,
        SUPPORTED_EXTENSIONS={
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".webp",
            ".heic",
            ".heif",
        },
    )
    found = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code" or "setup-install" in cell["metadata"].get(
            "tags", []
        ):
            continue
        source = "".join(cell["source"])
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                if node.name in found:
                    raise ValueError(f"Duplicate notebook definition: {node.name}")
                found[node.name] = node
                exec(
                    compile(
                        ast.Module(body=[node], type_ignores=[]), str(NOTEBOOK), "exec"
                    ),
                    namespace,
                )
            elif isinstance(node, ast.Assign) and all(
                isinstance(target, ast.Name) and target.id in CONSTANTS
                for target in node.targets
            ):
                exec(
                    compile(
                        ast.Module(body=[node], type_ignores=[]), str(NOTEBOOK), "exec"
                    ),
                    namespace,
                )
    if found.keys() != wanted:
        raise ValueError(f"Missing notebook definitions: {wanted - found.keys()}")
    return notebook, namespace, found


class ColabNotebookTests(unittest.TestCase):
    def setUp(self):
        self.notebook, self.ns, self.definitions = notebook_namespace()
        self.params = parameters()
        self.params["similarity"].update(timed_phash_threshold=3, phash_threshold=3)

    def test_core_definitions_match_app_source(self):
        for name in self.notebook["metadata"]["smart_gallery"]["app_core_functions"]:
            with self.subTest(name=name):
                source = parameter_module if name == "validate_parameters" else pipeline
                expected = ast.parse(inspect.getsource(getattr(source, name))).body[0]
                self.assertEqual(ast.dump(self.definitions[name]), ast.dump(expected))

    def test_parameter_snapshot_matches_its_recorded_provenance(self):
        snapshot = (ROOT / "colab" / "best_parameters.json").read_bytes()
        self.assertEqual(
            hashlib.sha256(snapshot).hexdigest(),
            self.notebook["metadata"]["smart_gallery"]["parameters_sha256"],
        )

    def test_current_flow_matches_app_with_both_linkages_and_time_policies(self):
        frames = [
            rows([0]),
            rows([0, 3, 15], times=[0, 20, 40]),
            rows([0, 1, 3, 7], times=[0, 1, 40, 41]),
            rows([0, (1 << 64) - 1, 0], times=[0, 1, 40]),
        ]
        missing = rows([0, 3, 0, 3], times=[0, 40, 0, 0])
        missing.loc[[2, 3], "taken_at"] = None
        frames.append(missing)
        for linkage in ("complete", "average"):
            for policy in ("strict", "phash"):
                for threshold in (None, 0, 3, 27):
                    params = copy.deepcopy(self.params)
                    params["similarity"].update(
                        linkage=linkage,
                        missing_exif_policy=policy,
                        timed_phash_threshold=threshold,
                    )
                    for index, frame in enumerate(frames):
                        with self.subTest(
                            linkage=linkage,
                            policy=policy,
                            threshold=threshold,
                            frame=index,
                        ):
                            actual = self.ns["run_core_pipeline"](frame.copy(), params)
                            expected = pipeline.run_core_pipeline(frame.copy(), params)
                            for left, right in zip(actual, expected):
                                pd.testing.assert_frame_equal(
                                    left, right, check_exact=True
                                )

    def test_folder_selection_accepts_a_number_or_custom_path(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            root = Path(directory)
            (root / "custom").mkdir()
            with patch("builtins.input", return_value="1"):
                self.assertEqual(
                    self.ns["choose_image_folder"]("", root), root.resolve()
                )
            with patch("builtins.input", return_value=str(root / "custom")):
                self.assertEqual(
                    self.ns["choose_image_folder"]("", root),
                    (root / "custom").resolve(),
                )

    def test_folder_outputs_keep_duplicate_names_skip_corrupt_files_and_match_app(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, stamp in [
                ("one", "2026:10:29 12:00:00"),
                ("two", "2026:10:29 12:00:40"),
            ]:
                (root / name).mkdir()
                (root / name / "same.jpg").write_bytes(jpeg_bytes(timestamp=stamp))
            (root / "broken.jpg").write_bytes(b"not an image")
            features, results, pairs, issues = self.ns["analyze_folder"](
                root, self.params
            )
            self.assertEqual(len(results), 2)
            self.assertEqual(results["filename"].tolist(), ["same.jpg", "same.jpg"])
            self.assertEqual(
                results["relative_path"].tolist(), ["one/same.jpg", "two/same.jpg"]
            )
            self.assertEqual(issues["filename"].tolist(), ["broken.jpg"])
            expected, expected_pairs = pipeline.analyze_features(features, self.params)
            pd.testing.assert_frame_equal(results, expected, check_exact=True)
            pd.testing.assert_frame_equal(pairs, expected_pairs, check_exact=True)
            images = []
            self.ns["display"] = images.append
            with redirect_stdout(io.StringIO()) as output:
                self.ns["show_photo_results"](results, max_images=1)
            self.assertEqual(len(images), 1)
            self.assertIn("คุณภาพ", output.getvalue())
            self.assertIn("ความคมชัด", output.getvalue())
            self.assertIn("แสง:", output.getvalue())
            self.assertIn("1 จาก 2", output.getvalue())

    def test_grouping_metrics_use_final_groups_and_unique_images_as_negatives(self):
        frame = rows([0] * 4)
        frame["source"] = ["similarity", "similarity", "unique", "unique"]
        frame["group_id"] = ["A", "A", None, None]
        frame["similarityGroup"] = ["G001", "G001", None, None]
        metrics = self.ns["grouping_metrics"](frame)
        self.assertEqual(metrics["pairs"], 6)
        self.assertEqual(metrics["positive_pairs"], 1)
        self.assertEqual(metrics["f1"], 1)
        self.assertEqual(metrics["adjusted_rand_index"], 1)
        frame.loc[2, "similarityGroup"] = "G001"
        metrics = self.ns["grouping_metrics"](frame)
        self.assertEqual(metrics["false_merge_pairs"], 2)
        self.assertAlmostEqual(metrics["precision"], 1 / 3)

    def test_evaluation_counts_all_four_sharpness_types_and_three_exposure_classes(self):
        frame = rows([0] * 210)
        frame["taken_at"] = None
        frame["source"] = ["sharpness"] * 120 + ["exposure"] * 90
        frame["group_id"] = None
        frame["blur_label"] = (
            ["Sharp"] * 30
            + ["Slight Blur"] * 30
            + ["Motion Blur"] * 30
            + ["Defocus Blur"] * 30
            + [None] * 90
        )
        frame["exposure_label"] = (
            [None] * 120
            + ["Normal"] * 30
            + ["Underexposed"] * 30
            + ["Overexposed"] * 30
        )
        threshold = self.params["sharpness"]["threshold"]
        frame["laplacian_score"] = [threshold * 2] * 30 + [threshold / 2] * 180
        # Deliberately misclassify one slight-blur image; it must still count.
        frame.loc[30, "laplacian_score"] = threshold * 2
        frame.loc[150:179, "brightness_mean"] = 0
        frame.loc[180:209, "brightness_mean"] = 255
        params = copy.deepcopy(self.params)
        params["similarity"]["missing_exif_policy"] = "strict"
        report = self.ns["evaluate_current_pipeline"](frame, params)

        counts = report["classification"].set_index("module")
        self.assertEqual(counts.loc["Sharpness (binary)", "images"], 120)
        self.assertAlmostEqual(counts.loc["Sharpness (binary)", "accuracy"], 119 / 120)
        self.assertEqual(counts.loc["Exposure", "images"], 90)
        self.assertEqual(counts.loc["Exposure", "accuracy"], 1)
        sharp_matrix = report["confusion_matrices"]["Sharpness (binary)"]
        exposure_matrix = report["confusion_matrices"]["Exposure"]
        self.assertEqual(sharp_matrix["labels"], ["Sharp", "Blur"])
        self.assertEqual(sharp_matrix["counts"].tolist(), [[30, 0], [1, 89]])
        self.assertEqual(exposure_matrix["counts"].tolist(), [[30, 0, 0], [0, 30, 0], [0, 0, 30]])
        by_type = report["sharpness_by_type"].set_index("dataset_type")
        self.assertEqual(by_type["images"].tolist(), [30] * 4)
        self.assertEqual(by_type["correct_binary_predictions"].tolist(), [30, 29, 30, 30])
        self.assertEqual(report["class_distribution"]["images"].sum(), 210)
        self.assertEqual(report["per_class"]["support"].sum(), 210)
        self.assertEqual(len(report["full_results"]), 210)

    def test_evaluation_normalizes_label_spellings_and_supports_legacy_blur(self):
        values = pd.Series(["Sharp", "Slight Blur", "motion-blur", "DEFOCUS_BLUR", "sligth_blur", "blur"])
        normalized = self.ns["normalize_evaluation_labels"](
            values, self.ns["SHARPNESS_BINARY_MAP"], "Sharpness"
        )
        self.assertEqual(normalized.tolist(), ["sharp", "slight_blur", "motion_blur", "defocus_blur", "slight_blur", "blur"])
        self.assertEqual(normalized.map(self.ns["SHARPNESS_BINARY_MAP"]).tolist(), ["sharp"] + ["blur"] * 5)

    def test_evaluation_rejects_missing_or_unknown_classes_instead_of_dropping_images(self):
        for source, column in [("sharpness", "blur_label"), ("exposure", "exposure_label")]:
            for invalid in (None, "unknown class"):
                with self.subTest(source=source, invalid=invalid):
                    frame = rows([0])
                    frame["source"] = source
                    frame[column] = invalid
                    with self.assertRaises(ValueError):
                        self.ns["evaluate_current_pipeline"](frame, self.params)

    def test_classification_matrix_keeps_classes_absent_from_a_split(self):
        _, per_class, matrix = self.ns["classification_outputs"](
            pd.Series(["normal"]), pd.Series(["normal"]),
            self.ns["EXPOSURE_CLASSES"],
            ["Normal", "Underexposed", "Overexposed"], "Exposure",
        )
        self.assertEqual(matrix["counts"].shape, (3, 3))
        self.assertEqual(matrix["counts"].sum(), 1)
        self.assertEqual(per_class["support"].tolist(), [1, 0, 0])

    def test_similarity_uses_twenty_groups_of_five_not_class_id_equality(self):
        frame = rows([0] * 102)
        frame["source"] = ["similarity"] * 100 + ["unique"] * 2
        frame["group_id"] = [f"GT-{i // 5}" for i in range(100)] + [None, None]
        frame["similarityGroup"] = [f"G{999 - i // 5}" for i in range(100)] + [None, None]
        metrics = self.ns["grouping_metrics"](frame)
        self.assertEqual(metrics["pairs"], 5151)
        self.assertEqual(metrics["positive_pairs"], 200)
        self.assertEqual(metrics["f1"], 1)
        self.assertEqual(metrics["adjusted_rand_index"], 1)
        self.assertEqual(metrics["false_merge_pairs"], 0)
        self.assertEqual(metrics["false_split_groups"], 0)
        frame["similarityGroup"] = None
        metrics = self.ns["grouping_metrics"](frame)
        self.assertEqual(metrics["false_split_pairs"], 200)
        self.assertEqual(metrics["false_split_groups"], 20)
        self.assertEqual(metrics["adjusted_rand_index"], 0)

    def test_best_shot_evaluation_counts_missed_and_multiple_selections(self):
        frame = rows([0, 0])
        frame["source"] = "similarity"
        frame["group_id"] = "A"
        frame["best_shot"] = [1, 0]
        for selections, expected in [
            ([True, False], 1),
            ([False, False], 0),
            ([True, True], 0),
        ]:
            with self.subTest(selections=selections):
                frame["bestShot"] = selections
                metrics = self.ns["best_shot_metrics"](frame)
                self.assertEqual(metrics["evaluated_groups"], 1)
                self.assertEqual(metrics["group_accuracy"], expected)

    def test_new_exports_preserve_original_files_and_serialize_reasons(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            root = Path(directory)
            results, pairs = self.ns["run_core_pipeline"](rows([0, 0]), self.params)
            destination = self.ns["export_results"](results, pairs, self.params, root)
            self.assertEqual(
                json.loads((destination / "parameters_used.json").read_text()),
                self.params,
            )
            exported = pd.read_csv(destination / "pipeline_results.csv")
            self.assertIsInstance(json.loads(exported.iloc[0]["reasons"]), list)
            self.assertTrue((destination / "similarity_pairs.csv").is_file())


if __name__ == "__main__":
    unittest.main()
