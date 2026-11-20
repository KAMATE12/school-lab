import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from school_lab.feature_cache import FeatureCache
from school_lab.quality_corpus import build_quality_data, write_quality_corpus
from school_lab.quality_experiment import (
    choose_threshold, evaluate, load_corpus, metrics, score_split, tune,
)


class QualityExperimentTests(unittest.TestCase):
    def test_metrics_and_abstentions_are_separate(self):
        # RU: Проверяем реальные счётчики, включая отказ от решения.
        # EN: Check actual counts, including abstention.
        rows = [dict(derivation_relation=truth, score=score) for truth, score in
                [(True, .8), (False, .7), (True, .4), (False, .1), (True, None), (False, None)]]
        result = metrics(rows, .6)
        self.assertEqual([result[k] for k in ("tp", "fp", "tn", "fn")], [1, 1, 1, 1])
        self.assertEqual(result["precision"], .5)
        self.assertEqual(result["recall"], .5)
        self.assertEqual(result["f1"], .5)
        self.assertEqual(result["indeterminate_fraction"], 2 / 6)
        self.assertEqual(result["indeterminate_positive"], 1)

    def test_undefined_metrics_are_not_fabricated(self):
        result = metrics([dict(derivation_relation=False, score=None)], .5)
        for key in ("precision", "recall", "f1"):
            self.assertIsNone(result[key])

    def test_evaluation_rows_cannot_tune_threshold(self):
        with self.assertRaises(ValueError):
            choose_threshold([dict(split="evaluation", derivation_relation=True, score=.7)])

    def test_tie_break_is_highest_threshold_after_equal_metrics(self):
        rows = [dict(split="tuning", derivation_relation=True, score=.8),
                dict(split="tuning", derivation_relation=False, score=.2)]
        self.assertEqual(choose_threshold(rows)["threshold"], .8)

    def test_tuning_does_not_prepare_evaluation_sources(self):
        data = build_quality_data()
        expected = score_split(data, "tuning")
        evaluation_ids = {p["submission_id"] for p in data["provenance"] if p["split"] == "evaluation"}
        for row in data["submissions"]:
            if row["submission_id"] in evaluation_ids:
                row["code"] = "def broken("
        self.assertEqual(score_split(data, "tuning"), expected)

    def test_all_fixed_pairs_are_scored_by_both_methods(self):
        rows = score_split(build_quality_data(), "evaluation")
        self.assertEqual(len(rows), 60)
        for method in ("token", "ast"):
            subset = [r for r in rows if r["method"] == method]
            self.assertEqual(len(subset), 30)
            self.assertEqual(sum(r["score"] is None for r in subset), 6)
            self.assertTrue(all(r["score"] is None for r in subset if r["template_only"]))

    def test_optimization_preserves_full_results(self):
        for split in ("tuning", "evaluation"):
            self.assertEqual(score_split(build_quality_data(), split), score_split(build_quality_data(), split, cached=True))

    def test_invalid_source_remains_structured_error(self):
        data = build_quality_data()
        data["submissions"][0]["code"] = "def broken("
        rows = score_split(data, "tuning")
        errors = [r for r in rows if r["status"] == "error"]
        self.assertEqual(len(errors), 8)
        self.assertTrue(all(r["score"] is None and r["errors"] for r in errors))

    def test_manifest_rejects_modified_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus"
            write_quality_corpus(path)
            load_corpus(path)
            with (path / "pairs.jsonl").open("a") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_corpus(path)

    def test_frozen_policy_cannot_be_modified(self):
        data = build_quality_data()
        policy = json.loads(json.dumps(tune(data, "fixture-hash")))
        result = evaluate(data, "fixture-hash", policy)
        self.assertTrue(result["optimization_equivalence"])
        policy["methods"]["token"]["threshold"] = -1
        with self.assertRaisesRegex(ValueError, "changed"):
            evaluate(data, "fixture-hash", policy)

    def test_frozen_policy_rejects_other_corpus(self):
        data = build_quality_data()
        with self.assertRaisesRegex(ValueError, "does not match"):
            evaluate(data, "other-hash", tune(data, "original-hash"))


class FeatureCacheTests(unittest.TestCase):
    def test_cache_reuses_exact_source_but_not_shifted_positions(self):
        for method in ("token", "ast"):
            cache = FeatureCache(method)
            original = cache.prepare("x = 1\n")
            self.assertIs(cache.prepare("x = 1\n"), original)
            shifted = cache.prepare("\nx = 1\n")
            self.assertEqual(original.keys, shifted.keys)
            self.assertNotEqual(original.occurrences, shifted.occurrences)
            self.assertEqual(cache.hits, 1)

    def test_template_is_part_of_cache_configuration(self):
        for method in ("token", "ast"):
            cache = FeatureCache(method)
            code = "x = 1\n"
            self.assertTrue(cache.prepare(code).keys)
            self.assertFalse(cache.prepare(code, code.strip()).keys)

    def test_cache_is_bounded_and_invalid_code_not_stored(self):
        cache = FeatureCache("token", capacity=1)
        cache.prepare("x = 1")
        cache.prepare("x = 2")
        cache.prepare("x = 1")
        self.assertEqual(cache.hits, 0)
        self.assertEqual(len(cache._items), 1)
        from school_lab.errors import SubmissionError
        with self.assertRaises(SubmissionError):
            cache.prepare("def broken(")
        self.assertEqual(len(cache._items), 1)


if __name__ == "__main__":
    unittest.main()
