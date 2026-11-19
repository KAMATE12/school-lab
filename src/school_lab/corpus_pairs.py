from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from school_lab.errors import SubmissionError
from school_lab.models import Submission
from school_lab.prepared_code import PreparedTokenCode, prepare_token_code


# RU: Связываем работу с её подготовленными признаками.
# EN: Associate a submission with its prepared features.
@dataclass(frozen=True)
class PreparedSubmission:
    submission: Submission
    features: PreparedTokenCode


# RU: Подготавливаем работы последовательно.
# EN: Prepare submissions sequentially.
def iter_prepared_submissions(
    submissions: Iterable[Submission],
    templates: Mapping[str, str],
) -> Iterator[PreparedSubmission]:
    for submission in submissions:
        # RU: Требуем явную конфигурацию задания.
        # EN: Require an explicit assignment configuration.
        if submission.assignment_id not in templates:
            raise SubmissionError(
                code="unknown_assignment",
                field="assignment_id",
                message=(
                    "Задание отсутствует в конфигурации / "
                    "Assignment is missing from the configuration"
                ),
            )

        template = templates[submission.assignment_id]
        features = prepare_token_code(submission.code, template)

        yield PreparedSubmission(
            submission=submission,
            features=features,
        )


# RU: Выдаём каждую допустимую пару один раз.
# EN: Yield each eligible pair once.
def iter_eligible_pairs(
    prepared: Iterable[PreparedSubmission],
) -> Iterator[tuple[PreparedSubmission, PreparedSubmission]]:
    # RU: Сохраняем ранее полученные работы по заданиям.
    # EN: Keep previously received submissions grouped by assignment.
    by_assignment: dict[str, list[PreparedSubmission]] = {}
    seen_ids: set[str] = set()

    for current in prepared:
        submission = current.submission

        # RU: Этот этап ожидает уже устранённые дубликаты.
        # EN: This stage expects duplicates to have been resolved already.
        if submission.submission_id in seen_ids:
            raise SubmissionError(
                code="duplicate_input",
                field="submission_id",
                message=(
                    "Повтор идентификатора во входном корпусе / "
                    "Repeated submission ID in the input corpus"
                ),
            )

        seen_ids.add(submission.submission_id)

        # RU: Получаем предыдущие работы только этого задания.
        # EN: Retrieve previous submissions for this assignment only.
        previous = by_assignment.setdefault(
            submission.assignment_id,
            [],
        )

        for other in previous:
            # RU: Пропускаем другие версии того же студента.
            # EN: Skip other versions belonging to the same student.
            if other.submission.student_id == submission.student_id:
                continue

            yield other, current

        # RU: Сохраняем текущую работу для следующих сравнений.
        # EN: Keep the current submission for later comparisons.
        previous.append(current)