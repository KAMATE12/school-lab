import copy
import unittest
from contextlib import redirect_stdout
from io import StringIO

# RU: Импортируем компоненты пакета для проверки приёма работ.
# EN: Import package components to test submission acceptance.
from school_lab.errors import SubmissionError
from school_lab.repository import InMemorySubmissionRepository
from school_lab.serialization import canonical_json
from school_lab.service import accept_submission
from school_lab.validation import parse_submission

# RU: Проверяем импорт строк через модуль пакета.
# EN: Test line importing through the package module.
from school_lab.importing import import_json_lines


# RU: Проверяем правила приёма работ.
# EN: Test the submission acceptance rules.
class ReceptionTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Перед каждым тестом создаём новые данные и хранилище.
        # EN: Create fresh data and a repository before each test.
        self.raw = {
            "schema_version": 1,
            "submission_id": "test-sub-001",
            "student_id": "test-student-001",
            "assignment_id": "test-assignment-01",
            "submitted_at": "2026-10-10T17:00:00+00:00",
            "text": "Test solution.",
            "code": "print(2 + 3)",
            "template_id": None,
            "ai_declaration": {
                "used": False,
                "tool": None,
                "purpose": None,
                "verified_by_student": True,
            },
        }

        self.repository = InMemorySubmissionRepository()
        self.submission = parse_submission(self.raw)

    def test_new_submission_is_stored(self) -> None:
        # RU: Новая работа должна быть сохранена.
        # EN: A new submission must be stored.
        accepted, is_duplicate = accept_submission(
            self.submission,
            self.repository,
        )

        self.assertFalse(is_duplicate)
        self.assertIs(accepted, self.submission)
        self.assertIs(
            self.repository.get(self.submission.submission_id),
            self.submission,
        )

    def test_duplicate_returns_original(self) -> None:
        # RU: Повторная работа должна вернуть исходный объект.
        # EN: A duplicate must return the original object.
        accept_submission(self.submission, self.repository)

        repeated = parse_submission(copy.deepcopy(self.raw))

        accepted, is_duplicate = accept_submission(
            repeated,
            self.repository,
        )

        self.assertIsNot(repeated, self.submission)
        self.assertTrue(is_duplicate)
        self.assertIs(accepted, self.submission)

    def test_conflict_preserves_original(self) -> None:
        # RU: Конфликт не должен заменять исходную работу.
        # EN: A conflict must not replace the original submission.
        accept_submission(self.submission, self.repository)

        changed_data = copy.deepcopy(self.raw)
        changed_data["code"] = "print(100)"
        changed = parse_submission(changed_data)

        with self.assertRaises(SubmissionError) as caught:
            accept_submission(changed, self.repository)

        self.assertEqual(caught.exception.code, "conflict")
        self.assertEqual(caught.exception.field, "submission_id")
        self.assertIs(
            self.repository.get(self.submission.submission_id),
            self.submission,
        )


    def test_import_continues_after_invalid_json(self) -> None:
        # RU: Создаём данные второй работы.
        # EN: Create the data for a second submission.
        second_data = copy.deepcopy(self.raw)
        second_data["submission_id"] = "test-sub-002"

        # RU: Помещаем ошибочную строку перед последней работой.
        # EN: Place an invalid line before the last submission.
        lines = [
            canonical_json(self.raw),
            canonical_json(self.raw),
            '{"schema_version":',
            canonical_json(second_data),
        ]

        # RU: Перехватываем сообщения импорта.
        # EN: Capture the import messages.
        output = StringIO()

        with redirect_stdout(output):
            summary = import_json_lines(lines, self.repository)

        # RU: Проверяем итоговые счётчики.
        # EN: Check the final counters.
        self.assertEqual(
            summary,
            {
                "accepted": 2,
                "duplicate": 1,
                "errors": 1,
            },
        )

        # RU: Проверяем сохранение работы после ошибочной строки.
        # EN: Check that the submission after the invalid line was stored.
        stored = self.repository.get("test-sub-002")

        self.assertIsNotNone(stored)
        self.assertEqual(
            stored,
            parse_submission(second_data),
        )

        # RU: Проверяем номер строки и тип ошибки в сообщении.
        # EN: Check the line number and error type in the message.
        self.assertIn(
            "Line 3: error code=invalid_json, field=json",
            output.getvalue(),
        )

    


if __name__ == "__main__":
    unittest.main()
