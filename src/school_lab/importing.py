# RU: Принимаем любой источник, который предоставляет строки.
# EN: Accept any source that provides strings through iteration.
from collections.abc import Iterable

# RU: Используем ошибки, хранилище, сервис и проверку данных.
# EN: Use errors, the repository, the service, and data validation.
from school_lab.errors import SubmissionError
from school_lab.repository import InMemorySubmissionRepository
from school_lab.service import accept_submission
from school_lab.validation import decode_json, parse_submission

# RU: Обрабатываем строки JSON независимо друг от друга.
# EN: Process JSON lines independently.
def import_json_lines(
    lines: Iterable[str],
    repository: InMemorySubmissionRepository
) -> dict[str, int]:
    # RU: Создаём счётчики результатов.
    # EN: Create result counters.
    counts = {
        "accepted": 0,
        "duplicate": 0,
        "errors": 0
    }

    for line_number, line in enumerate(lines, start=1):
        try:
            # RU: Читаем JSON, проверяем данные и принимаем работу.
            # EN: Decode JSON, validate the data, and accept the submission.
            raw = decode_json(line)
            submission = parse_submission(raw)
            stored, is_duplicate = accept_submission(
                submission,
                repository
            )

        except SubmissionError as error:
            # RU: Записываем ошибку и продолжаем обработку.
            # EN: Record the error and continue processing.
            counts["errors"] += 1

            print(
                f"Line {line_number}: error "
                f"code={error.code}, field={error.field}"
            )
            print("Message:", error.message)

        else:
            if is_duplicate:
                counts["duplicate"] += 1
                status = "duplicate"
            else:
                counts["accepted"] += 1
                status = "accepted"

            print(
                f"Line {line_number}: {status} "
                f"id={stored.submission_id}"
            )

    return counts
