import unittest

# RU: Проверяем анализ декларации через общий сервис.
# EN: Test declaration analysis through the shared service.
from school_lab.analysis_service import analyze_submission
from school_lab.models import (
    AIDeclaration,
    AnalysisContext,
    Assignment,
    Submission,
)


class AIDeclarationAnalyzerTests(unittest.TestCase):
    def make_submission(self, verified: bool) -> Submission:
        # RU: Создаём корректный пример с заявленным использованием ИИ.
        # EN: Create a valid example with declared AI usage.
        return Submission(
            schema_version=1,
            submission_id="ai-sub-001",
            student_id="student-001",
            assignment_id="assignment-01",
            submitted_at="2026-10-10T17:00:00+00:00",
            text="Explanation.",
            code="print(2 + 3)",
            template_id=None,
            ai_declaration=AIDeclaration(
                used=True,
                tool="ChatGPT",
                purpose="Explain an error",
                verified_by_student=verified,
            ),
        )

    def setUp(self) -> None:
        # RU: Создаём контекст задания перед каждым тестом.
        # EN: Create the assignment context before each test.
        self.context = AnalysisContext(
            assignment=Assignment(
                assignment_id="assignment-01",
                allowed_template="",
                requirements=(),
            )
        )

    def test_unverified_declaration_requires_review(self) -> None:
        # RU: Без подтверждённой проверки требуется просмотр.
        # EN: Review is required without declared student verification.
        submission = self.make_submission(verified=False)

        report = analyze_submission(
            submission,
            self.context,
            "ai_declaration",
        )

        self.assertEqual(report.analyzer_id, "ai_declaration")
        self.assertTrue(report.review_required)
        self.assertEqual(len(report.findings), 1)

        finding = report.findings[0]
        self.assertIsNone(finding.score)
        self.assertEqual(finding.evidence, ())
        self.assertIn("ChatGPT", finding.explanation)
        self.assertIn("Explain an error", finding.explanation)

    def test_verified_declaration_does_not_trigger_this_rule(self) -> None:
        # RU: Заявленная проверка не активирует это правило просмотра.
        # EN: Declared verification does not trigger this review rule.
        submission = self.make_submission(verified=True)

        report = analyze_submission(
            submission,
            self.context,
            "ai_declaration",
        )

        self.assertFalse(report.review_required)
        self.assertIn(
            "does not prove",
            report.findings[0].explanation,
        )


if __name__ == "__main__":
    unittest.main()
