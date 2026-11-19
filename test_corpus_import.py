import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from school_lab.corpus_comparison import iter_token_comparisons
from school_lab.corpus_import import (
    CorpusImportStats,
    iter_imported_prepared,
)
from school_lab.errors import SubmissionError
from school_lab.prepared_code import prepare_token_code


class CorpusImportTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Создаём исходную корректную запись.
        # EN: Create the initial valid record.
        self.raw = {
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
        }

    def test_mixed_import_continues_and_preserves_original(self) -> None:
        # RU: Создаём конфликтующую запись с тем же идентификатором.
        # EN: Create a conflicting record with the same identifier.
        conflict = deepcopy(self.raw)
        conflict["code"] = "value = 999\n"

        # RU: Создаём отдельную работу с ошибкой синтаксиса.
        # EN: Create a separate submission with invalid syntax.
        invalid_code = deepcopy(self.raw)
        invalid_code["submission_id"] = "B"
        invalid_code["student_id"] = "student-2"
        invalid_code["code"] = "print("

        # RU: Последняя корректная работа должна быть обработана.
        # EN: The final valid submission must still be processed.
        last = deepcopy(self.raw)
        last["submission_id"] = "C"
        last["student_id"] = "student-3"

        lines = [
            json.dumps(self.raw),
            json.dumps(self.raw),
            "{broken",
            json.dumps(conflict),
            json.dumps(invalid_code),
            json.dumps(last),
        ]

        stats = CorpusImportStats()
        errors: list[tuple[int, str]] = []

        # RU: Собираем ошибки вместо вывода на экран.
        # EN: Collect errors instead of printing them.
        def record_error(
            line_number: int,
            error: SubmissionError,
        ) -> None:
            errors.append((line_number, error.code))

        prepared = list(iter_imported_prepared(
            lines,
            {"assignment-1": ""},
            stats,
            record_error,
        ))

        self.assertEqual(
            [item.submission.submission_id for item in prepared],
            ["A", "C"],
        )
        self.assertEqual(prepared[0].submission.code, "value = 2\n")
        self.assertEqual(
            errors,
            [
                (3, "invalid_json"),
                (4, "conflict"),
                (5, "invalid_code"),
            ],
        )
        self.assertEqual(
            (stats.accepted, stats.prepared, stats.duplicate, stats.errors),
            (3, 2, 1, 3),
        )

        # RU: Сравниваем только две успешно подготовленные работы.
        # EN: Compare only the two successfully prepared submissions.
        comparisons = list(iter_token_comparisons(prepared))

        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0].score, 1.0)

    def test_duplicate_is_not_prepared_again(self) -> None:
        # RU: Повторяем одну и ту же входную запись.
        # EN: Repeat the same input record.
        line = json.dumps(self.raw)
        stats = CorpusImportStats()

        def unexpected_error(
            line_number: int,
            error: SubmissionError,
        ) -> None:
            self.fail(f"Unexpected error on line {line_number}: {error.code}")

        # RU: Считаем вызовы настоящей функции подготовки.
        # EN: Count calls to the real preparation function.
        with patch(
            "school_lab.corpus_import.prepare_token_code",
            wraps=prepare_token_code,
        ) as preparation:
            prepared = list(iter_imported_prepared(
                [line, line],
                {"assignment-1": ""},
                stats,
                unexpected_error,
            ))

        self.assertEqual(len(prepared), 1)
        self.assertEqual(preparation.call_count, 1)
        self.assertEqual(stats.duplicate, 1)
        self.assertEqual(stats.errors, 0)


if __name__ == "__main__":
    unittest.main()