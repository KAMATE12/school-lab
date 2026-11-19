import unittest
from collections.abc import Iterator

from school_lab.pipeline import iter_validated_submissions


class PipelineTests(unittest.TestCase):
    def test_reads_only_when_requested(self) -> None:
        # RU: Запоминаем номера строк, предоставленных источником.
        # EN: Record the line numbers supplied by the source.
        supplied_lines: list[int] = []

        # RU: Создаём наблюдаемый источник из двух строк.
        # EN: Create an observable source containing two lines.
        def source() -> Iterator[str]:
            supplied_lines.append(1)
            yield "{broken"

            supplied_lines.append(2)
            yield "{}"

        # RU: Создаём конвейер без чтения строк.
        # EN: Create the pipeline without reading any lines.
        results = iter_validated_submissions(source())
        self.assertEqual(supplied_lines, [])

        # RU: Запрашиваем только первый результат.
        # EN: Request only the first result.
        first = next(results)

        self.assertEqual(supplied_lines, [1])
        self.assertEqual(first.line_number, 1)
        self.assertIsNone(first.submission)
        self.assertIsNotNone(first.error)
        self.assertEqual(first.error.code, "invalid_json")

        # RU: После первой ошибки запрашиваем второй результат.
        # EN: Request the second result after the first error.
        second = next(results)

        self.assertEqual(supplied_lines, [1, 2])
        self.assertEqual(second.line_number, 2)
        self.assertIsNone(second.submission)
        self.assertIsNotNone(second.error)
        self.assertEqual(second.error.code, "schema_error")

        # RU: Проверяем завершение источника после двух строк.
        # EN: Check that the source ends after two lines.
        with self.assertRaises(StopIteration):
            next(results)


if __name__ == "__main__":
    unittest.main()