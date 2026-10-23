# RU: Используем модели, хранилище и вычисление хеша.
# EN: Use models, storage, and hash computation.
from school_lab.errors import SubmissionError
from school_lab.models import Submission
from school_lab.repository import InMemorySubmissionRepository
from school_lab.serialization import submission_hash


# RU: Принимаем работу с проверкой дубликатов и конфликтов.
# EN: Accept a submission while checking duplicates and conflicts.
def accept_submission(
    submission: Submission,
    repository: InMemorySubmissionRepository,
) -> tuple[Submission, bool]:
    # RU: Ищем работу с таким же идентификатором.
    # EN: Look for a submission with the same identifier.
    existing = repository.get(submission.submission_id)

    if existing is None:
        # RU: Сохраняем новую работу.
        # EN: Store the new submission.
        repository.add(submission)
        return submission, False

    # RU: Сравниваем хеши сохранённой и полученной работ.
    # EN: Compare the stored and incoming submission hashes.
    existing_hash = submission_hash(existing)
    incoming_hash = submission_hash(submission)

    if existing_hash == incoming_hash:
        # RU: Возвращаем ранее сохранённый объект без замены.
        # EN: Return the previously stored object without replacing it.
        return existing, True

    # RU: Отклоняем другой контент с тем же идентификатором.
    # EN: Reject different content with the same identifier.
    raise SubmissionError(
        code="conflict",
        field="submission_id",
        message=(
            "Этот идентификатор уже используется для другой работы / "
            "This identifier is already used for a different submission"
        ),
    )
