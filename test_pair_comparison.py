import unittest
from dataclasses import replace

from school_lab.errors import SubmissionError
from school_lab.pair_comparison import compare_token_submissions
from school_lab.validation import parse_submission


class PairComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Создаём корректную синтетическую работу.
        # EN: Create a valid synthetic submission.
        self.first = parse_submission({
            "schema_version": 1,
            "submission_id": "pair-001",
            "student_id": "student-001",
            "assignment_id": "assignment-01",
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

        # RU: Создаём работу другого студента с тем же кодом.
        # EN: Create another student's submission with identical code.
        self.second = replace(
            self.first,
            submission_id="pair-002",
            student_id="student-002",
        )

    def test_identical_code_has_score_one_and_original_positions(self) -> None:
        # RU: Разные номера строк не меняют содержимое признаков.
        # EN: Different line numbers do not change feature content.
        second = replace(
            self.second,
            code="# Heading\n\nvalue = 2\n",
        )

        result = compare_token_submissions(self.first, second)

        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.first_matches[0].start_line, 1)
        self.assertEqual(result.second_matches[0].start_line, 3)
        self.assertEqual(
            result.first_matches[0].key,
            result.second_matches[0].key,
        )

    def test_ineligible_pairs_are_rejected(self) -> None:
        # RU: Проверяем самосравнение, другое задание и того же студента.
        # EN: Check self-match, another assignment, and the same student.
        cases = (
            (self.first, "self_match"),
            (
                replace(self.second, assignment_id="assignment-02"),
                "assignment_mismatch",
            ),
            (
                replace(self.second, student_id=self.first.student_id),
                "same_student",
            ),
        )

        for second, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(SubmissionError) as caught:
                    compare_token_submissions(self.first, second)

                self.assertEqual(caught.exception.code, expected_code)

    def test_template_only_is_insufficient_data(self) -> None:
        # RU: После исключения шаблона сравнивать больше нечего.
        # EN: After excluding the template, nothing remains to compare.
        template = "from typing import Iterable\n"
        first = replace(self.first, code=template)
        second = replace(self.second, code=template)

        result = compare_token_submissions(first, second, template)

        self.assertIsNone(result.score)
        self.assertEqual(result.first_matches, ())
        self.assertEqual(result.second_matches, ())
        self.assertEqual(result.first_template_lines, (1,))
        self.assertEqual(result.second_template_lines, (1,))

    def test_template_does_not_hide_other_identical_code(self) -> None:
        # RU: Сохраняем совпадение самостоятельного кода вне шаблона.
        # EN: Preserve matching code outside the template.
        template = "from typing import Iterable\n"
        code = template + "value = 2\n"
        first = replace(self.first, code=code)
        second = replace(self.second, code=code)

        result = compare_token_submissions(first, second, template)

        self.assertEqual(result.score, 1.0)
        self.assertEqual(len(result.first_matches), 1)
        self.assertEqual(result.first_matches[0].start_line, 2)
        self.assertEqual(result.first_matches[0].end_line, 2)

    def test_invalid_code_keeps_structured_error(self) -> None:
        # RU: Не превращаем синтаксическую ошибку в числовой score.
        # EN: Do not turn a syntax error into a numeric score.
        second = replace(self.second, code="print(")

        with self.assertRaises(SubmissionError) as caught:
            compare_token_submissions(self.first, second)

        self.assertEqual(caught.exception.code, "invalid_code")


if __name__ == "__main__":
    unittest.main()