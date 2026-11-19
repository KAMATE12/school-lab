import unittest
from dataclasses import replace
from unittest.mock import patch

from school_lab.corpus_comparison import (
    compare_prepared_submissions,
    iter_token_comparisons,
)
from school_lab.corpus_pairs import iter_prepared_submissions
from school_lab.errors import SubmissionError
from school_lab.pair_comparison import compare_token_submissions
from school_lab.validation import parse_submission


class CorpusComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Создаём два проверенных примера разных студентов.
        # EN: Create two validated examples from different students.
        self.first = parse_submission({
            "schema_version": 1,
            "submission_id": "A",
            "student_id": "student-1",
            "assignment_id": "assignment-1",
            "submitted_at": "2026-10-10T17:00:00+00:00",
            "text": "Example.",
            "code": "value = 2\n",
            "template_id": None,
            "ai_declaration": {
                "used": False,
                "tool": None,
                "purpose": None,
                "verified_by_student": True,
            },
        })
        self.second = replace(
            self.first,
            submission_id="B",
            student_id="student-2",
            code="# Heading\nvalue = 2\n",
        )

    def test_prepared_comparison_matches_direct_comparison(self) -> None:
        # RU: Проверяем сохранение score и исходных позиций.
        # EN: Check preservation of the score and original positions.
        prepared = list(iter_prepared_submissions(
            [self.first, self.second],
            {"assignment-1": ""},
        ))

        direct = compare_token_submissions(self.first, self.second)
        reused = compare_prepared_submissions(
            prepared[0],
            prepared[1],
        )

        self.assertEqual(reused, direct)

    def test_comparison_does_not_extract_tokens_again(self) -> None:
        # RU: Сначала полностью подготавливаем три работы.
        # EN: Fully prepare three submissions first.
        third = replace(
            self.first,
            submission_id="C",
            student_id="student-3",
            code="value = 3\n",
        )
        prepared = list(iter_prepared_submissions(
            [self.first, self.second, third],
            {"assignment-1": ""},
        ))

        # RU: Повторное извлечение токенов должно вызвать ошибку теста.
        # EN: Any repeated token extraction must fail the test.
        with patch(
            "school_lab.prepared_code.extract_code_tokens",
            side_effect=AssertionError("Unexpected token extraction"),
        ):
            results = list(iter_token_comparisons(prepared))

        self.assertEqual(
            [(item.first_id, item.second_id) for item in results],
            [("A", "B"), ("A", "C"), ("B", "C")],
        )
        self.assertEqual(
            [item.score for item in results],
            [1.0, 0.0, 0.0],
        )

    def test_different_template_configurations_are_rejected(self) -> None:
        # RU: Подготавливаем работы с разными настройками шаблона.
        # EN: Prepare submissions with different template settings.
        first = next(iter_prepared_submissions(
            [self.first],
            {"assignment-1": ""},
        ))
        second = next(iter_prepared_submissions(
            [self.second],
            {"assignment-1": "value = 2\n"},
        ))

        with self.assertRaises(SubmissionError) as caught:
            compare_prepared_submissions(first, second)

        self.assertEqual(
            caught.exception.code,
            "configuration_mismatch",
        )


if __name__ == "__main__":
    unittest.main()