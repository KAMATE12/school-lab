import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# RU: Подготавливаем входной JSON с правилами проекта.
# EN: Prepare input JSON using the project's formatting rules.
from school_lab.serialization import canonical_json


class AnalysisCliTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Создаём корректную работу для проверки команды.
        # EN: Create a valid submission for testing the command.
        self.raw = {
            "schema_version": 1,
            "submission_id": "cli-sub-001",
            "student_id": "student-001",
            "assignment_id": "assignment-01",
            "submitted_at": "2026-10-10T17:00:00+00:00",
            "text": "Explanation.",
            "code": "print(1)",
            "template_id": None,
            "ai_declaration": {
                "used": False,
                "tool": None,
                "purpose": None,
                "verified_by_student": True,
            },
        }

    def run_cli(
        self,
        input_path: Path,
        output_path: Path,
        analyzers: tuple[str, ...],
    ) -> subprocess.CompletedProcess[str]:
        # RU: Используем тот же Python, который выполняет тесты.
        # EN: Use the same Python interpreter that runs the tests.
        command = [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "school_lab.analyze_cli",
            str(input_path),
            "--assignment-id",
            "assignment-01",
            "--output",
            str(output_path),
        ]

        # RU: Добавляем выбранные анализаторы к аргументам.
        # EN: Add the selected analyzers to the arguments.
        for analyzer_id in analyzers:
            command.extend(["--analyzer", analyzer_id])

        # RU: Запускаем команду и сохраняем её вывод и код завершения.
        # EN: Run the command and capture its output and exit code.
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=False,
            cwd=input_path.parent,
        )

    def test_valid_input_produces_two_reports(self) -> None:
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            input_path = folder / "input.jsonl"
            output_path = folder / "reports.jsonl"

            input_path.write_text(
                canonical_json(self.raw) + "\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                input_path,
                output_path,
                ("length", "ai_declaration"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)

            # RU: Проверяем реальные отчёты, записанные командой.
            # EN: Check the actual reports written by the command.
            reports = [
                json.loads(line)
                for line in output_path.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]

            self.assertEqual(len(reports), 2)
            self.assertEqual(
                [report["analyzer_id"] for report in reports],
                ["length", "ai_declaration"],
            )

            for report in reports:
                self.assertEqual(
                    report["submission_id"],
                    "cli-sub-001",
                )

    def test_invalid_line_does_not_stop_next_submission(self) -> None:
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            input_path = folder / "input.jsonl"
            output_path = folder / "reports.jsonl"

            # RU: Ошибочная строка расположена перед корректной работой.
            # EN: The invalid line comes before the valid submission.
            input_path.write_text(
                '{"broken":\n' + canonical_json(self.raw) + "\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                input_path,
                output_path,
                ("length",),
            )

            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("Line 1: invalid_json", result.stderr)

            report_lines = output_path.read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(len(report_lines), 1)
            self.assertEqual(
                json.loads(report_lines[0])["submission_id"],
                "cli-sub-001",
            )

    def test_existing_output_is_preserved(self) -> None:
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            input_path = folder / "input.jsonl"
            output_path = folder / "reports.jsonl"

            input_path.write_text(
                canonical_json(self.raw) + "\n",
                encoding="utf-8",
            )

            # RU: Создаём существующий файл, который нельзя перезаписывать.
            # EN: Create an existing file that must not be overwritten.
            original_content = "Existing report content\n"
            output_path.write_text(original_content, encoding="utf-8")

            result = self.run_cli(
                input_path,
                output_path,
                ("length",),
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                original_content,
            )


if __name__ == "__main__":
    unittest.main()
