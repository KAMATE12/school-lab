# RU: Проверяем связь отчёта с работой и границы подтверждений.
# EN: Check the report's submission association and evidence bounds.
import math
import re
from datetime import datetime
from school_lab.models import Finding, Evidence
from school_lab.errors import SubmissionError
from school_lab.models import AnalysisContext, AnalysisReport, Submission
from school_lab.serialization import submission_hash


# RU: Создаём структурированную ошибку отчёта.
# EN: Create a structured report error.
def invalid_report(field: str, message: str) -> SubmissionError:
    return SubmissionError(
        code="invalid_report",
        field=field,
        message=message,
    )


# RU: Проверяем результат перед его передачей пользователю.
# EN: Validate the result before passing it to the user.
def validate_report(
    report: AnalysisReport,
    submission: Submission,
    context: AnalysisContext,
    analyzer_id: str,
) -> None:
    if not isinstance(report, AnalysisReport):
        raise invalid_report(
            "report",
            "Ожидается AnalysisReport / An AnalysisReport is required",
        )

    # RU: Проверяем метаданные и типы контейнеров отчёта.
    # EN: Validate report metadata and container types.
    for field in ("report_id", "analyzer_id", "analyzer_version", "created_at"):
        value = getattr(report, field)
        if not isinstance(value, str) or not value.strip():
            raise invalid_report(field, "Ожидается непустая строка / Non-empty string required")
    for field in ("submission_hash", "config_hash"):
        value = getattr(report, field)
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise invalid_report(field, "Неверный SHA-256 / Invalid SHA-256")
    try:
        created = datetime.fromisoformat(report.created_at)
    except ValueError as error:
        raise invalid_report("created_at", "Неверная дата / Invalid timestamp") from error
    if created.utcoffset() is None:
        raise invalid_report("created_at", "Нужен часовой пояс / Time zone required")
    if type(report.review_required) is not bool or not isinstance(report.findings, tuple):
        raise invalid_report("report", "Неверные типы / Invalid types")

    # RU: Проверяем идентификаторы и хеш анализируемой работы.
    # EN: Check identifiers and the analyzed submission hash.
    if report.submission_id != submission.submission_id:
        raise invalid_report(
            "submission_id",
            "Неверная работа / Incorrect submission",
        )

    if report.submission_hash != submission_hash(submission):
        raise invalid_report(
            "submission_hash",
            "Неверный хеш работы / Incorrect submission hash",
        )

    if report.analyzer_id != analyzer_id:
        raise invalid_report(
            "analyzer_id",
            "Неверный анализатор / Incorrect analyzer",
        )

    # RU: Собираем работы, на которые разрешено ссылаться.
    # EN: Collect submissions that evidence may reference.
    available = {}

    for item in (*context.submissions, submission):
        previous = available.get(item.submission_id)

        if previous is not None and previous != item:
            raise invalid_report(
                "evidence",
                "Неоднозначный идентификатор / Ambiguous submission ID",
            )

        available[item.submission_id] = item

    for finding in report.findings:
        if not isinstance(finding, Finding):
            raise invalid_report("findings", "Ожидается Finding / Finding required")
        if finding.kind not in ("similarity", "rubric_feedback", "processing_error"):
            raise invalid_report("finding.kind", "Неизвестный вид / Unknown kind")
        if not isinstance(finding.explanation, str) or not finding.explanation.strip():
            raise invalid_report("finding.explanation", "Нужно пояснение / Explanation required")
        if finding.score is not None and (
            type(finding.score) not in (int, float) or not math.isfinite(finding.score)
        ):
            raise invalid_report("finding.score", "Неверная оценка / Invalid score")
        if not isinstance(finding.evidence, tuple):
            raise invalid_report("finding.evidence", "Ожидается tuple / Tuple required")
        for evidence in finding.evidence:
            if not isinstance(evidence, Evidence) or not isinstance(evidence.submission_id, str):
                raise invalid_report("evidence", "Неверное подтверждение / Invalid evidence")
            target = available.get(evidence.submission_id)

            if target is None:
                raise invalid_report(
                    "evidence.submission_id",
                    "Неизвестная работа / Unknown submission",
                )

            if evidence.field not in ("text", "code"):
                raise invalid_report(
                    "evidence.field",
                    "Неизвестное поле / Unknown field",
                )

            # RU: Требуем целые номера строк, исключая bool.
            # EN: Require integer line numbers, excluding bool.
            if (
                type(evidence.start_line) is not int
                or type(evidence.end_line) is not int
            ):
                raise invalid_report(
                    "evidence.lines",
                    "Ожидаются целые числа / Integers are required",
                )

            line_count = len(
                getattr(target, evidence.field).splitlines()
            )

            # RU: Обе границы включены и относятся к исходным строкам.
            # EN: Both bounds are inclusive and refer to original lines.
            if not (
                1 <= evidence.start_line
                <= evidence.end_line
                <= line_count
            ):
                raise invalid_report(
                    "evidence.lines",
                    "Строки вне допустимых границ / Lines are out of bounds",
                )
