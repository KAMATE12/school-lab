import unittest

# RU: Используем анализатор, модели и хеширование.
# EN: Use the analyzer, models, and hashing.
from school_lab.analyzers import LengthAnalyzer
from school_lab.models import (
    AIDeclaration,
    AnalysisContext,
    Assignment,
    Submission,
)
from school_lab.serialization import submission_hash


# RU: Проверяем подсчёт строк и ссылки на исходный код.
# EN: Test line counting and references to the original code.
class LengthAnalyzerTests(unittest.TestCase):
    def test_counts_nonempty_lines_and_preserves_positions(self) -> None:
        # RU: В коде есть пустая строка между двумя инструкциями.
        # EN: The code has an empty line between two statements.
        submission = Submission(
            schema_version=1,
            submission_id="analysis-sub-001",
            student_id="student-001",
            assignment_id="assignment-01",
            submitted_at="2026-10-10T17:00:00+00:00",
            text="Explanation.\n   \nConclusion.",
            code="print(1)\n\nprint(2)",
            template_id=None,
            ai_declaration=AIDeclaration(
                used=False,
                tool=None,
                purpose=None,
                verified_by_student=True,
            ),
        )

        context = AnalysisContext(
            assignment=Assignment(
                assignment_id="assignment-01",
                allowed_template="",
                requirements=("Provide an explanation and code.",),
            )
        )

        original_hash = submission_hash(submission)

        # RU: Запускаем анализ и получаем первое наблюдение.
        # EN: Run the analysis and obtain the first finding.
        report = LengthAnalyzer().analyze(submission, context)

        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]

        self.assertEqual(report.analyzer_id, "length")
        self.assertEqual(report.submission_hash, original_hash)
        self.assertEqual(submission_hash(submission), original_hash)
        self.assertIsNone(finding.score)
        self.assertIn("text=2, code=2", finding.explanation)

        # RU: Проверяем исходные номера строк обоих полей.
        # EN: Check the original line numbers in both fields.
        positions = []

        for evidence in finding.evidence:
            self.assertEqual(
                evidence.submission_id,
                submission.submission_id,
            )
            positions.append(
                (
                    evidence.field,
                    evidence.start_line,
                    evidence.end_line,
                )
            )

        self.assertEqual(
            positions,
            [
                ("text", 1, 1),
                ("text", 3, 3),
                ("code", 1, 1),
                ("code", 3, 3),
            ],
        )


if __name__ == "__main__":
    unittest.main()
