import copy
import unittest

# RU: Используем ошибки, сериализацию и проверку данных.
# EN: Use errors, serialization, and data validation.
from school_lab.errors import SubmissionError
from school_lab.serialization import canonical_json, submission_hash
from school_lab.validation import decode_json, parse_submission


# RU: Проверяем правила входных данных.
# EN: Test the input data rules.
class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Перед каждым тестом создаём корректные данные.
        # EN: Create valid data before each test.
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

    def test_validation_preserves_input(self) -> None:
        # RU: Проверка не должна изменять исходные данные.
        # EN: Validation must not modify the input data.
        before = copy.deepcopy(self.raw)

        parse_submission(self.raw)

        self.assertEqual(self.raw, before)

    def test_missing_and_unknown_fields(self) -> None:
        # RU: Проверяем отсутствующее и неизвестное поля.
        # EN: Check a missing field and an unknown field.
        missing = copy.deepcopy(self.raw)
        del missing["student_id"]

        unknown = copy.deepcopy(self.raw)
        unknown["student_age"] = 25

        cases = [
            (missing, "student_id"),
            (unknown, "student_age"),
        ]

        for data, expected_field in cases:
            with self.subTest(field=expected_field):
                with self.assertRaises(SubmissionError) as caught:
                    parse_submission(data)

                self.assertEqual(caught.exception.code, "schema_error")
                self.assertEqual(caught.exception.field, expected_field)

    def test_invalid_field_values(self) -> None:
        # RU: Проверяем несколько недопустимых значений.
        # EN: Check several invalid values.
        cases = [
            ("schema_version", True, "schema_error", "schema_version"),
            ("schema_version", 2, "unsupported_version", "schema_version"),
            ("student_id", "   ", "schema_error", "student_id"),
            ("template_id", "", "schema_error", "template_id"),
            (
                "submitted_at",
                "2026-10-10T17:00:00",
                "schema_error",
                "submitted_at",
            ),
        ]

        for field, value, expected_code, expected_field in cases:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.raw)
                data[field] = value

                with self.assertRaises(SubmissionError) as caught:
                    parse_submission(data)

                self.assertEqual(caught.exception.code, expected_code)
                self.assertEqual(caught.exception.field, expected_field)

    def test_empty_content_is_rejected(self) -> None:
        # RU: Текст и код не могут одновременно быть пустыми.
        # EN: Text and code cannot both be empty.
        self.raw["text"] = "   "
        self.raw["code"] = "\n"

        with self.assertRaises(SubmissionError) as caught:
            parse_submission(self.raw)

        self.assertEqual(caught.exception.code, "schema_error")
        self.assertEqual(caught.exception.field, "text/code")

    def test_ai_usage_requires_tool_and_purpose(self) -> None:
        # RU: При использовании ИИ нужны инструмент и цель.
        # EN: AI usage requires both a tool and a purpose.
        self.raw["ai_declaration"]["used"] = True

        with self.assertRaises(SubmissionError) as caught:
            parse_submission(self.raw)

        self.assertEqual(caught.exception.code, "schema_error")
        self.assertEqual(caught.exception.field, "ai_declaration")

    def test_invalid_json_is_rejected(self) -> None:
        # RU: Проверяем синтаксис, повтор ключа и константы.
        # EN: Check syntax, a repeated key, and special constants.
        invalid_inputs = [
            '{"schema_version":',
            '{"student_id":"a","student_id":"b"}',
            '{"value":NaN}',
            '{"value":Infinity}',
            '{"value":-Infinity}',
        ]

        for text in invalid_inputs:
            with self.subTest(text=text):
                with self.assertRaises(SubmissionError) as caught:
                    decode_json(text)

                self.assertEqual(caught.exception.code, "invalid_json")

    def test_key_order_does_not_change_hash(self) -> None:
        # RU: Меняем порядок ключей, сохраняя те же данные.
        # EN: Change key order while preserving the same data.
        reordered = dict(reversed(list(self.raw.items())))

        first = parse_submission(decode_json(canonical_json(self.raw)))
        second = parse_submission(decode_json(canonical_json(reordered)))

        self.assertEqual(submission_hash(first), submission_hash(second))

    def test_content_change_changes_hash(self) -> None:
        # RU: Изменение кода должно изменить хеш этого примера.
        # EN: Changing the code must change this example's hash.
        changed = copy.deepcopy(self.raw)
        changed["code"] = "print(100)"

        first = parse_submission(self.raw)
        second = parse_submission(changed)

        self.assertNotEqual(submission_hash(first), submission_hash(second))


if __name__ == "__main__":
    unittest.main()
