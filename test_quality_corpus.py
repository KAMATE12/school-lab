import ast
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from school_lab.quality_corpus import (
    build_quality_data, validate_quality_data, corpus_files,
    rename_identifiers, write_quality_corpus,
)


class QualityCorpusTests(unittest.TestCase):
    def setUp(self):
        self.data = build_quality_data()

    # RU: Проверяем реальные требования к размеру и разделению корпуса.
    # EN: Check actual corpus size and split requirements.
    def test_counts_and_family_disjointness(self):
        result = validate_quality_data(self.data)
        self.assertEqual((result["submissions"],result["families"],result["pairs"]),(44,20,60))
        families = {split: {m["family_id"] for m in self.data["provenance"] if m["split"] == split}
                    for split in ("tuning","evaluation")}
        self.assertFalse(families["tuning"] & families["evaluation"])
        for split in ("tuning","evaluation"):
            self.assertEqual(result["splits"][split],dict(pairs=30,positive=18,negative=12,template_only=6))

    def test_family_leakage_is_rejected(self):
        self.data["provenance"][1]["split"]="evaluation"
        with self.assertRaisesRegex(ValueError,"Family leakage"):
            validate_quality_data(self.data)

    def test_pair_crossing_splits_is_rejected(self):
        pair=self.data["pairs"][0]
        pair["second_id"]="sum_squares-family-04-base"
        with self.assertRaisesRegex(ValueError,"Pair crosses splits"):
            validate_quality_data(self.data)

    def test_wrong_derivation_label_is_rejected(self):
        self.data["pairs"][0]["derivation_relation"]=False
        with self.assertRaisesRegex(ValueError,"Derivation label"):
            validate_quality_data(self.data)

    def test_wrong_template_label_is_rejected(self):
        self.data["pairs"][0]["template_only"]=True
        with self.assertRaisesRegex(ValueError,"Template-only label"):
            validate_quality_data(self.data)

    def test_reversed_duplicate_pair_is_rejected(self):
        pair=copy.deepcopy(self.data["pairs"][0])
        pair["first_id"],pair["second_id"]=pair["second_id"],pair["first_id"]
        self.data["pairs"].append(pair)
        with self.assertRaisesRegex(ValueError,"Duplicate unordered pair"):
            validate_quality_data(self.data)

    def test_parent_and_recorded_transformation_are_checked(self):
        self.data["submissions"][1]["code"] += "unexpected = 1\n"
        with self.assertRaisesRegex(ValueError,"recorded transformation"):
            validate_quality_data(self.data)

    def test_template_control_cannot_hide_extra_code(self):
        self.data["submissions"][-1]["code"] += "value = 7\n"
        with self.assertRaisesRegex(ValueError,"additional code"):
            validate_quality_data(self.data)

    def test_renaming_preserves_strings_comments_and_unmatched_names(self):
        code='value = "value"  # value\nvalue2 = value\n'
        renamed=rename_identifiers(code,{"value":"number"})
        self.assertEqual(renamed,'number = "value"  # value\nvalue2 = number\n')
        ast.parse(renamed)

    def test_missing_provenance_and_non_boolean_labels_are_rejected(self):
        bad=copy.deepcopy(self.data);bad["provenance"].pop()
        with self.assertRaisesRegex(ValueError,"Missing provenance"):
            validate_quality_data(bad)
        self.data["pairs"][0]["derivation_relation"]=1
        with self.assertRaisesRegex(ValueError,"Labels must be booleans"):
            validate_quality_data(self.data)

    def test_generation_is_deterministic_and_uses_no_similarity_scores(self):
        with patch("school_lab.ast_features.prepare_ast_code", side_effect=AssertionError("Do not score labels")), \
             patch("school_lab.prepared_code.prepare_token_code", side_effect=AssertionError("Do not score labels")):
            first=corpus_files(build_quality_data())
            second=corpus_files(build_quality_data())
        self.assertEqual(first,second)

    def test_repeated_build_preserves_files_and_rejects_modified_corpus(self):
        with tempfile.TemporaryDirectory() as folder:
            destination=Path(folder)/"corpus"
            first=write_quality_corpus(destination)
            before={p.name:p.read_bytes() for p in destination.iterdir()}
            self.assertEqual(first,write_quality_corpus(destination))
            self.assertEqual(before,{p.name:p.read_bytes() for p in destination.iterdir()})
            path=destination/"pairs.jsonl";path.write_text("modified by user",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Existing corpus differs"):
                write_quality_corpus(destination)
            self.assertEqual(path.read_text(),"modified by user")

if __name__=="__main__":
    unittest.main()
