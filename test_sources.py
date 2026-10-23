import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# RU: Проверяем обе реализации общего интерфейса.
# EN: Test both implementations of the shared interface.
from school_lab.sources import InMemoryLineSource, JsonlFileSource


class LineSourceTests(unittest.TestCase):
    def test_sources_preserve_lines_and_can_reopen(self) -> None:
        # RU: Используем Unicode и намеренно некорректную строку JSON.
        # EN: Use Unicode and an intentionally invalid JSON line.
        expected = [
            '{"text":"Привет"}\n',
            '{"broken":\n',
        ]

        # RU: Создаём временный файл, удаляемый после теста.
        # EN: Create a temporary file removed after the test.
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text("".join(expected), encoding="utf-8")

            sources = [
                InMemoryLineSource(expected),
                JsonlFileSource(path),
            ]

            # RU: Применяем одинаковые проверки к обоим источникам.
            # EN: Apply identical checks to both sources.
            for source in sources:
                with self.subTest(source=type(source).__name__):
                    for _ in range(2):
                        with source.open() as lines:
                            self.assertEqual(list(lines), expected)

    def test_file_closes_after_early_exit(self) -> None:
        # RU: Читаем только первую строку и выходим из контекста.
        # EN: Read only the first line and leave the context.
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text("first\nsecond\n", encoding="utf-8")
            source = JsonlFileSource(path)

            with source.open() as lines:
                self.assertEqual(next(lines), "first\n")
                self.assertFalse(lines.closed)

            self.assertTrue(lines.closed)

    def test_file_closes_when_processing_raises(self) -> None:
        # RU: Имитируем ошибку в коде, использующем источник.
        # EN: Simulate an error in the code consuming the source.
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text("first\n", encoding="utf-8")
            source = JsonlFileSource(path)

            with self.assertRaises(RuntimeError):
                with source.open() as lines:
                    next(lines)
                    raise RuntimeError("Processing failed")

            self.assertTrue(lines.closed)


if __name__ == "__main__":
    unittest.main()
