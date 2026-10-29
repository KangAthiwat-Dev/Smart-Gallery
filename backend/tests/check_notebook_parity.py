"""Compare inspected notebook core functions with the production pipeline.

Run from backend:
    python tests/check_notebook_parity.py --notebook /path/presentation_results.ipynb

Only named, reviewed core function definitions are loaded; notebook setup,
experiments, save operations and evaluation cells are never executed.
"""

import argparse
import ast
import copy
import json
from itertools import combinations
from pathlib import Path

import imagehash
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering

from app.services import pipeline
from fixtures import latest_parameters
from test_latest_algorithm import rows

FUNCTIONS = {
    "_time_difference_seconds",
    "build_similarity_groups",
    "add_best_shot_and_recommendation",
    "rescue_borderline_singletons",
    "merge_nearby_similarity_groups",
    "apply_group_merge_safety_guard",
    "apply_rescue_safety_guard",
    "run_core_pipeline",
    "classify_sharpness",
    "classify_exposure",
    "sharpness_score_0_100",
    "exposure_score_0_100",
    "add_quality_scores",
}


def notebook_functions(path):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    definitions = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        # Parse only cells defining an expected core function.
        if not any(f"def {name}(" in source for name in FUNCTIONS):
            continue
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS:
                if node.name in definitions:
                    raise ValueError(f"Duplicate core function: {node.name}")
                definitions[node.name] = node
    if set(definitions) != FUNCTIONS:
        raise ValueError(f"Missing core functions: {FUNCTIONS - definitions.keys()}")
    namespace = {
        "np": np,
        "pd": pd,
        "imagehash": imagehash,
        "combinations": combinations,
        "AgglomerativeClustering": AgglomerativeClustering,
    }
    for node in definitions.values():
        exec(
            compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"),
            namespace,
        )
    return namespace


def assert_same(actual, expected):
    if isinstance(actual, tuple):
        for left, right in zip(actual, expected, strict=True):
            assert_same(left, right)
    else:
        pd.testing.assert_frame_equal(actual, expected, check_exact=True)


def check(path):
    notebook = notebook_functions(path)
    count = 0

    def compare(name, *args, **kwargs):
        nonlocal count
        actual = getattr(pipeline, name)(*copy.deepcopy(args), **copy.deepcopy(kwargs))
        expected = notebook[name](*copy.deepcopy(args), **copy.deepcopy(kwargs))
        assert_same(actual, expected)
        count += 1
        return actual

    features = {
        "single": rows([0]),
        "average-distance": rows([0, 3, 15]),
        "rescue": rows([0, 1, 2, 15]),
        "group-merge": rows([0] * 5, times=[0, 10, 20, 40, 50]),
        "random": rows(list(np.random.default_rng(29).integers(0, 2**32, size=30))),
    }
    missing = rows([0] * 4)
    missing.loc[[0, 2], "taken_at"] = None
    features["missing-exif"] = missing
    for linkage in ("complete", "average"):
        params = latest_parameters()
        params["similarity"].update(phash_threshold=3, linkage=linkage)
        for frame in features.values():
            compare("add_quality_scores", frame, params)
            compare("build_similarity_groups", frame, params)
            for rescue, merge in (
                (False, None),
                (True, False),
                (True, None),
                (False, True),
            ):
                compare(
                    "run_core_pipeline",
                    frame,
                    params,
                    use_rescue=rescue,
                    use_group_merge=merge,
                )

    params = latest_parameters()
    params["similarity"]["phash_threshold"] = 3
    for score in (50, 100):
        before = rows([0, 1, 2, 15], ["G001"] * 3 + [None], [90, 70, 60, score])
        grouped, log = compare("rescue_borderline_singletons", before, params)
        result = compare("add_best_shot_and_recommendation", grouped, params)
        compare("apply_rescue_safety_guard", result, before, log, params)
    for second_best in (80, 89.8):
        before = rows(
            [0] * 5,
            ["G001"] * 3 + ["G002"] * 2,
            [90, 70, 60, second_best, 50],
            [0, 10, 20, 40, 50],
        )
        grouped, log = compare("merge_nearby_similarity_groups", before, params)
        result = compare("add_best_shot_and_recommendation", grouped, params)
        compare("apply_group_merge_safety_guard", result, before, log, params)
    compare(
        "add_best_shot_and_recommendation",
        rows([0] * 3, ["G001"] * 3, [90, 89.8, 70]),
        params,
    )
    print(f"PASS: {count} exact DataFrame comparisons with {path.name}")
    print(
        "Includes both linkages, missing EXIF, ties, singleton rescue, group merge, safety guards and baseline toggles."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, required=True)
    check(parser.parse_args().notebook)
