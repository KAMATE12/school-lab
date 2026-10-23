# RU: Используем хеширование, время UTC, протоколы и идентификаторы.
# EN: Use hashing, UTC timestamps, protocols, and identifiers.
import hashlib
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

# RU: Используем общие модели, ошибки и сериализацию.
# EN: Use shared models, errors, and serialization.
from school_lab.errors import SubmissionError
from school_lab.models import (
    AnalysisContext,
    AnalysisReport,
    Evidence,
    Finding,
    Submission,
)
from school_lab.serialization import canonical_json, submission_hash


# RU: Описываем общий интерфейс анализатора.
# EN: Describe the common analyzer interface.
class Analyzer(Protocol):
    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        ...


# RU: Подсчитываем непустые строки текста и кода.
# EN: Count non-empty text and code lines.
class LengthAnalyzer:
    analyzer_id = "length"
    analyzer_version = "1.0.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        # RU: Проверяем соответствие работы заданию.
        # EN: Check that the submission matches the assignment.
        if submission.assignment_id != context.assignment.assignment_id:
            raise SubmissionError(
                code="assignment_mismatch",
                field="assignment_id",
                message=(
                    "Работа относится к другому заданию / "
                    "The submission belongs to a different assignment"
                ),
            )

        # RU: Создаём отдельные счётчики и список подтверждений.
        # EN: Create separate counters and a list of supporting references.
        counts = {"text": 0, "code": 0}
        evidence_items: list[Evidence] = []

        # RU: Обрабатываем исходные поля без изменения их содержимого.
        # EN: Process original fields without modifying their content.
        for field in ("text", "code"):
            content = getattr(submission, field)

            for line_number, line in enumerate(
                content.splitlines(),
                start=1,
            ):
                # RU: Пропускаем строки, содержащие только пробелы.
                # EN: Skip whitespace-only lines.
                if line.strip() == "":
                    continue

                counts[field] += 1

                # RU: Сохраняем исходный номер непустой строки.
                # EN: Preserve the original non-empty line number.
                evidence_items.append(
                    Evidence(
                        submission_id=submission.submission_id,
                        field=field,
                        start_line=line_number,
                        end_line=line_number,
                    )
                )

        # RU: Формируем наблюдение без числовой оценки.
        # EN: Create a finding without a numerical score.
        finding = Finding(
            kind="rubric_feedback",
            score=None,
            evidence=tuple(evidence_items),
            explanation=(
                "Непустые строки / Non-empty lines: "
                f"text={counts['text']}, code={counts['code']}. "
                "Количество строк не определяет качество решения / "
                "Line count does not determine solution quality."
            ),
        )

        # RU: Фиксируем правила подсчёта в конфигурации.
        # EN: Record the counting rules in the configuration.
        config = {
            "fields": ["text", "code"],
            "ignore_whitespace_only": True,
        }
        config_bytes = canonical_json(config).encode("utf-8")
        config_hash = hashlib.sha256(config_bytes).hexdigest()

        # RU: Создаём отчёт с идентификаторами и временем UTC.
        # EN: Create a report with identifiers and a UTC timestamp.
        return AnalysisReport(
            report_id=str(uuid4()),
            submission_id=submission.submission_id,
            submission_hash=submission_hash(submission),
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            config_hash=config_hash,
            findings=(finding,),
            created_at=datetime.now(timezone.utc).isoformat(),
            review_required=True,
        )

# RU: Находим точные вхождения разрешённого шаблона.
# EN: Find exact occurrences of the allowed template.
class TemplateAnalyzer:
    analyzer_id = "template"
    analyzer_version = "1.0.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        # RU: Проверяем соответствие заданию.
        # EN: Check that the assignment matches.
        if submission.assignment_id != context.assignment.assignment_id:
            raise SubmissionError(
                code="assignment_mismatch",
                field="assignment_id",
                message=(
                    "Работа относится к другому заданию / "
                    "The submission belongs to a different assignment"
                ),
            )

        template = context.assignment.allowed_template
        evidence_items: list[Evidence] = []

        # RU: Пустой шаблон не создаёт совпадений.
        # EN: An empty or whitespace-only template produces no matches.
        if template.strip() != "":
            template_lines = template.splitlines()
            width = len(template_lines)

            for field in ("text", "code"):
                original_lines = getattr(submission, field).splitlines()

                # RU: Проверяем все позиции, где помещается весь шаблон.
                # EN: Check every position where the whole template fits.
                for start in range(len(original_lines) - width + 1):
                    candidate = original_lines[start:start + width]

                    # RU: Сравниваем строки без удаления пробелов.
                    # EN: Compare lines without removing whitespace.
                    if candidate == template_lines:
                        evidence_items.append(
                            Evidence(
                                submission_id=submission.submission_id,
                                field=field,
                                start_line=start + 1,
                                end_line=start + width,
                            )
                        )

        # RU: Объясняем результат без вывода о плагиате.
        # EN: Explain the result without a plagiarism verdict.
        if template.strip() == "":
            explanation = (
                "Разрешённый шаблон не задан / "
                "No allowed template was provided."
            )
        elif evidence_items:
            explanation = (
                "Найдены точные блоки разрешённого шаблона / "
                "Exact allowed-template blocks found: "
                f"{len(evidence_items)}. "
                "Это разрешённое совпадение / "
                "These matches come from the allowed template."
            )
        else:
            explanation = (
                "Точный блок шаблона не найден / "
                "No exact template block was found. "
                "Это не доказывает оригинальность / "
                "This does not prove originality."
            )

        finding = Finding(
            kind="similarity",
            score=None,
            evidence=tuple(evidence_items),
            explanation=explanation,
        )

        # RU: Включаем шаблон и правило поиска в конфигурацию.
        # EN: Include the template and matching rule in the configuration.
        config = {
            "allowed_template": template,
            "matching": "exact_contiguous_lines",
            "fields": ["text", "code"],
        }
        config_hash = hashlib.sha256(
            canonical_json(config).encode("utf-8")
        ).hexdigest()

        # RU: Создаём отчёт с исходными позициями совпадений.
        # EN: Create a report with original match positions.
        return AnalysisReport(
            report_id=str(uuid4()),
            submission_id=submission.submission_id,
            submission_hash=submission_hash(submission),
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            config_hash=config_hash,
            findings=(finding,),
            created_at=datetime.now(timezone.utc).isoformat(),
            review_required=True,
        )

# RU: Анализируем декларацию использования ИИ.
# EN: Analyze the AI usage declaration.
class AIDeclarationAnalyzer:
    analyzer_id = "ai_declaration"
    analyzer_version = "1.0.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        # RU: Проверяем соответствие работы заданию.
        # EN: Check that the submission matches the assignment.
        if submission.assignment_id != context.assignment.assignment_id:
            raise SubmissionError(
                code="assignment_mismatch",
                field="assignment_id",
                message=(
                    "Работа относится к другому заданию / "
                    "The submission belongs to a different assignment"
                ),
            )

        declaration = submission.ai_declaration
        # RU: Проверяем обязательные сведения даже при прямом создании модели.
        # EN: Check required details even for directly constructed models.
        if declaration.used and any(
            not isinstance(value, str) or not value.strip()
            for value in (declaration.tool, declaration.purpose)
        ):
            raise SubmissionError(
                "schema_error", "ai_declaration",
                "Укажите инструмент и цель / Provide tool and purpose",
            )

        # RU: Описываем заявленное использование ИИ.
        # EN: Describe the declared AI usage.
        if declaration.used:
            usage_message = (
                "Заявлено использование ИИ / AI usage declared. "
                f"Инструмент / Tool: {declaration.tool}. "
                f"Цель / Purpose: {declaration.purpose}."
            )
        else:
            usage_message = (
                "Студент заявил, что ИИ не использовался / "
                "The student declared that AI was not used."
            )

        # RU: Отдельно описываем заявленную проверку результата.
        # EN: Separately describe the declared verification of the result.
        if declaration.verified_by_student:
            verification_message = (
                "Студент заявил о проверке результата / "
                "The student declared that the result was verified."
            )
        else:
            verification_message = (
                "Проверка студентом не подтверждена; требуется просмотр / "
                "Student verification is not confirmed; review is required."
            )

        # RU: Не выдаём декларацию за доказательство правильности.
        # EN: Do not present the declaration as proof of correctness.
        explanation = (
            f"{usage_message} {verification_message} "
            "Декларация не доказывает правильность работы / "
            "The declaration does not prove that the submission is correct."
        )

        finding = Finding(
            kind="rubric_feedback",
            score=None,
            evidence=(),
            explanation=explanation,
        )

        # RU: Фиксируем правило принятия решения о просмотре.
        # EN: Record the rule used to request review.
        config = {
            "review_if_unverified": True,
            "source": "student_declaration",
        }
        config_hash = hashlib.sha256(
            canonical_json(config).encode("utf-8")
        ).hexdigest()

        # RU: Создаём отчёт без оценки и вымышленных ссылок на строки.
        # EN: Create a report without a score or invented line references.
        return AnalysisReport(
            report_id=str(uuid4()),
            submission_id=submission.submission_id,
            submission_hash=submission_hash(submission),
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            config_hash=config_hash,
            findings=(finding,),
            created_at=datetime.now(timezone.utc).isoformat(),
            review_required=not declaration.verified_by_student,
        )
