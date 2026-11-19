from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass

from school_lab.corpus_pairs import PreparedSubmission
from school_lab.errors import SubmissionError
from school_lab.pipeline import iter_validated_submissions
from school_lab.prepared_code import prepare_token_code
from school_lab.repository import InMemorySubmissionRepository
from school_lab.service import accept_submission


# RU: Храним счётчики текущего запуска.
# EN: Store counters for the current run.
@dataclass
class CorpusImportStats:
    accepted: int = 0
    prepared: int = 0
    duplicate: int = 0
    errors: int = 0


# RU: Импортируем и подготавливаем работы по одной.
# EN: Import and prepare submissions one at a time.
def iter_imported_prepared(
    lines: Iterable[str],
    templates: Mapping[str, str],
    stats: CorpusImportStats,
    on_error: Callable[[int, SubmissionError], None],
) -> Iterator[PreparedSubmission]:
    repository = InMemorySubmissionRepository()

    for result in iter_validated_submissions(lines):
        # RU: Сообщаем об ошибке JSON или схемы и продолжаем.
        # EN: Report a JSON or schema error and continue.
        if result.error is not None:
            stats.errors += 1
            on_error(result.line_number, result.error)
            continue

        submission = result.submission

        # RU: Защищаем внутренний контракт результата проверки.
        # EN: Protect the internal validation-result contract.
        if submission is None:
            raise RuntimeError("Missing submission after successful validation")

        try:
            # RU: Повторно используем правила дубликатов и конфликтов.
            # EN: Reuse duplicate and conflict handling.
            stored, is_duplicate = accept_submission(
                submission,
                repository,
            )

            if is_duplicate:
                stats.duplicate += 1
                continue

            stats.accepted += 1

            # RU: Проверяем наличие конфигурации задания.
            # EN: Check that assignment configuration exists.
            if stored.assignment_id not in templates:
                raise SubmissionError(
                    code="unknown_assignment",
                    field="assignment_id",
                    message=(
                        "Неизвестное задание / "
                        "Unknown assignment"
                    ),
                )

            features = prepare_token_code(
                stored.code,
                templates[stored.assignment_id],
            )

        except SubmissionError as error:
            # RU: Ошибка одной работы не останавливает импорт.
            # EN: One submission error does not stop the import.
            stats.errors += 1
            on_error(result.line_number, error)
            continue

        # RU: Передаём только успешно подготовленную работу.
        # EN: Yield only a successfully prepared submission.
        stats.prepared += 1
        yield PreparedSubmission(
            submission=stored,
            features=features,
        )