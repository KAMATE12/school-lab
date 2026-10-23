# RU: Описываем функции, создающие анализаторы.
# EN: Describe callables that create analyzers.
from collections.abc import Callable

from school_lab.errors import SubmissionError
from school_lab.models import AnalysisContext, AnalysisReport, Submission

# RU: Импортируем общий интерфейс и доступные анализаторы.
# EN: Import the shared interface and available analyzers.
from school_lab.analyzers import (
    Analyzer,
    AIDeclarationAnalyzer,
    LengthAnalyzer,
    TemplateAnalyzer,
)

# RU: Защищаем исходные данные и проверяем отчёт.
# EN: Protect the original data and validate the report.
from copy import deepcopy
from school_lab.report_validation import validate_report


# RU: Связываем имена с фабриками анализаторов.
# EN: Associate names with analyzer factories.
ANALYZER_FACTORIES: dict[str, Callable[[], Analyzer]] = {
    "length": LengthAnalyzer,
    "template": TemplateAnalyzer,
    "ai_declaration": AIDeclarationAnalyzer,
}


# RU: Запускаем анализатор и проверяем его результат.
# EN: Run the analyzer and validate its result.
def analyze_submission(
    submission: Submission,
    context: AnalysisContext,
    analyzer_id: str,
) -> AnalysisReport:
    factory = ANALYZER_FACTORIES.get(analyzer_id)

    if factory is None:
        raise SubmissionError(
            code="unknown_analyzer",
            field="analyzer_id",
            message=(
                "Неизвестный анализатор / "
                f"Unknown analyzer: {analyzer_id}"
            ),
        )

    # RU: Передаём анализатору независимые копии входных объектов.
    # EN: Give the analyzer independent copies of the input objects.
    working_submission, working_context = deepcopy(
        (submission, context)
    )

    try:
        analyzer = factory()
        report = analyzer.analyze(
            working_submission,
            working_context,
        )

        # RU: Проверяем, что анализатор не изменил свои входные данные.
        # EN: Check that the analyzer did not modify its input data.
        if (
            working_submission != submission
            or working_context != context
        ):
            raise SubmissionError(
                code="analyzer_mutation",
                field="analysis",
                message=(
                    "Анализатор изменил данные / "
                    "The analyzer modified its input"
                ),
            )

        validate_report(
            report,
            submission,
            context,
            analyzer_id,
        )

    except SubmissionError:
        # RU: Сохраняем уже структурированные ошибки.
        # EN: Preserve errors that are already structured.
        raise

    except Exception as error:
        # RU: Преобразуем неожиданную ошибку компонента.
        # EN: Convert an unexpected component failure.
        raise SubmissionError(
            code="analyzer_error",
            field=analyzer_id,
            message=(
                "Ошибка анализатора / Analyzer failed: "
                f"{type(error).__name__}: {error}"
            ),
        ) from error

    return report
