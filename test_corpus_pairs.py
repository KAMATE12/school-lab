import unittest
from dataclasses import replace

from school_lab.corpus_pairs import (
    iter_eligible_pairs,
    iter_prepared_submissions,
)
from school_lab.errors import SubmissionError
from school_lab.validation import parse_submission


class CorpusPairsTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Создаём проверенную синтетическую работу.
        # EN: Create a validated synthetic submission.
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

    def test_only_eligible_pairs_are_produced_once(self) -> None:
        # RU: Включаем другую версию студента и другое задание.
        # EN: Include another student version and another assignment.
        submissions = [
            self.first,
            replace(
                self.first,
                submission_id="B",
                student_id="student-2",
            ),
            replace(self.first, submission_id="C"),
            replace(
                self.first,
                submission_id="D",
                student_id="student-3",
                assignment_id="assignment-2",
            ),
        ]

        prepared = iter_prepared_submissions(
            submissions,
            {"assignment-1": "", "assignment-2": ""},
        )
        pairs = list(iter_eligible_pairs(prepared))

        self.assertEqual(
            [
                (left.submission.submission_id,
                 right.submission.submission_id)
                for left, right in pairs
            ],
            [("A", "B"), ("B", "C")],
        )

        # RU: Объект B повторно используется без новой подготовки.
        # EN: Object B is reused without preparing it again.
        self.assertIs(pairs[0][1], pairs[1][0])

    def test_repeated_submission_id_is_rejected(self) -> None:
        # RU: Защищаем выбор пар от повторяющихся идентификаторов.
        # EN: Protect pair selection against repeated identifiers.
        prepared = iter_prepared_submissions(
            [self.first, self.first],
            {"assignment-1": ""},
        )

        with self.assertRaises(SubmissionError) as caught:
            list(iter_eligible_pairs(prepared))

        self.assertEqual(caught.exception.code, "duplicate_input")

    def test_unknown_assignment_is_rejected(self) -> None:
        # RU: Не допускаем отсутствующую конфигурацию задания.
        # EN: Reject missing assignment configuration.
        prepared = iter_prepared_submissions([self.first], {})

        with self.assertRaises(SubmissionError) as caught:
            next(prepared)

        self.assertEqual(caught.exception.code, "unknown_assignment")


if __name__ == "__main__":
    unittest.main()