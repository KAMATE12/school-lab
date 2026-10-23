import unittest
from dataclasses import replace
from unittest.mock import patch

from school_lab.analysis_service import (
    ANALYZER_FACTORIES,
    analyze_submission,
)
from school_lab.analyzers import LengthAnalyzer
from school_lab.errors import SubmissionError
from school_lab.models import (
    AIDeclaration,
    AnalysisContext,
    Assignment,
    Evidence,
    Submission,
)


# RU: Имитируем анализатор, который аварийно завершается.
# EN: Simulate an analyzer that fails unexpectedly.
class FailingAnalyzer:
    def analyze(self, submission, context):
        raise RuntimeError("Example failure")


# RU: Имитируем анализатор с неправильной ссылкой на строку.
# EN: Simulate an analyzer with an incorrect line reference.
class InvalidEvidenceAnalyzer:
    def analyze(self, submission, context):
        report = LengthAnalyzer().analyze(submission, context)

        invalid_evidence = Evidence(
            submission_id=submission.submission_id,
            field="code",
            start_line=999,
            end_line=999,
        )

        finding = replace(
            report.findings[0],
            evidence=(invalid_evidence,),
        )

        return replace(
            report,
            analyzer_id="invalid_evidence",
            findings=(finding,),
        )


class AnalysisServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Готовим корректную работу и контекст.
        # EN: Prepare a valid submission and context.
        self.submission = Submission(
            schema_version=1,
            submission_id="service-sub-001",
            student_id="student-001",
            assignment_id="assignment-01",
            submitted_at="2026-10-10T17:00:00+00:00",
            text="Explanation.",
            code="print(1)",
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
                allowed_template="",
                requirements=(),
            )
        )

    def test_unexpected_failure_becomes_structured_error(self) -> None:
        # RU: Временно добавляем тестовый анализатор в реестр.
        # EN: Temporarily add the test analyzer to the registry.
        with patch.dict(
            ANALYZER_FACTORIES,
            {"failing": FailingAnalyzer},
        ):
            with self.assertRaises(SubmissionError) as caught:
                analyze_submission(
                    self.submission, self.context, "failing"
                )

        self.assertEqual(caught.exception.code, "analyzer_error")

    def test_out_of_bounds_evidence_is_rejected(self) -> None:
        # RU: Проверяем отклонение несуществующей строки.
        # EN: Check rejection of a nonexistent line.
        with patch.dict(
            ANALYZER_FACTORIES,
            {"invalid_evidence": InvalidEvidenceAnalyzer},
        ):
            with self.assertRaises(SubmissionError) as caught:
                analyze_submission(
                    self.submission,
                    self.context,
                    "invalid_evidence",
                )

        self.assertEqual(caught.exception.code, "invalid_report")
        self.assertEqual(caught.exception.field, "evidence.lines")


if __name__ == "__main__":
    unittest.main()
