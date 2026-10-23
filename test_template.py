import unittest
from dataclasses import replace

# RU: Проверяем выбор анализатора и позиции шаблона.
# EN: Test analyzer selection and template positions.
from school_lab.analysis_service import analyze_submission
from school_lab.errors import SubmissionError
from school_lab.models import (
    AIDeclaration,
    AnalysisContext,
    Assignment,
    Submission,
)


class TemplateAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Шаблон занимает вторую и третью строки кода.
        # EN: The template occupies code lines two and three.
        self.submission = Submission(
            schema_version=1,
            submission_id="template-sub-001",
            student_id="student-001",
            assignment_id="assignment-01",
            submitted_at="2026-10-10T17:00:00+00:00",
            text="Explanation.",
            code="# Start\ndef solve():\n    pass\nprint('Done')",
            template_id=None,
            ai_declaration=AIDeclaration(
                used=False,
                tool=None,
                purpose=None,
                verified_by_student=True,
            ),
        )

        self.context = AnalysisContext(
            assignment=Assignment(
                assignment_id="assignment-01",
                allowed_template="def solve():\n    pass",
                requirements=(),
            )
        )

    def test_exact_template_positions(self) -> None:
        # RU: Запускаем анализатор через общий сервис.
        # EN: Run the analyzer through the shared service.
        report = analyze_submission(
            self.submission, self.context, "template"
        )

        self.assertEqual(report.analyzer_id, "template")
        finding = report.findings[0]
        self.assertIsNone(finding.score)
        self.assertEqual(len(finding.evidence), 1)

        evidence = finding.evidence[0]
        self.assertEqual(evidence.field, "code")
        self.assertEqual(evidence.start_line, 2)
        self.assertEqual(evidence.end_line, 3)

    def test_changed_indentation_does_not_match(self) -> None:
        # RU: Создаём новый объект с другим отступом.
        # EN: Create a new object with different indentation.
        changed = replace(
            self.submission,
            code="def solve():\n  pass",
        )

        report = analyze_submission(changed, self.context, "template")

        self.assertEqual(report.findings[0].evidence, ())

    def test_unknown_analyzer_is_rejected(self) -> None:
        # RU: Неизвестное имя должно вызвать структурированную ошибку.
        # EN: An unknown name must cause a structured error.
        with self.assertRaises(SubmissionError) as caught:
            analyze_submission(
                self.submission, self.context, "unknown"
            )

        self.assertEqual(caught.exception.code, "unknown_analyzer")


if __name__ == "__main__":
    unittest.main()
