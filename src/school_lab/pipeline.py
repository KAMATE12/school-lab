# RU: Импортируем типы для последовательного чтения.
# EN: Import types for sequential reading.
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

# RU: Повторно используем модели и проверки первой лабораторной.
# EN: Reuse the models and validation from laboratory 1.
from school_lab.errors import SubmissionError
from school_lab.models import Submission
from school_lab.validation import decode_json, parse_submission


# RU: Храним результат проверки одной строки.
# EN: Store the validation result for one line.
@dataclass(frozen=True)
class ValidationResult:
    line_number: int
    submission: Submission | None
    error: SubmissionError | None


# RU: Проверяем строки по запросу, не собирая все результаты в список.
# EN: Validate lines on demand without collecting all results in a list.
def iter_validated_submissions(
    lines: Iterable[str],
) -> Iterator[ValidationResult]:
    for line_number, line in enumerate(lines, start=1):
        try:
            # RU: Преобразуем JSON-текст в объект Python.
            # EN: Convert JSON text into a Python object.
            raw_data = decode_json(line)

            # RU: Проверяем данные и создаём объект Submission.
            # EN: Validate the data and create a Submission object.
            submission = parse_submission(raw_data)

        except SubmissionError as error:
            # RU: Передаём ошибку вместе с номером строки.
            # EN: Yield the error together with the line number.
            yield ValidationResult(
                line_number=line_number,
                submission=None,
                error=error,
            )

        else:
            # RU: Передаём проверенную работу.
            # EN: Yield the validated submission.
            yield ValidationResult(
                line_number=line_number,
                submission=submission,
                error=None,
            )