# RU: Используем общую ошибку и модель работы.
# EN: Use the shared error and submission model.
from school_lab.errors import SubmissionError
from school_lab.models import Submission


# RU: Храним работы в памяти по их идентификаторам.
# EN: Store submissions in memory by their identifiers.
class InMemorySubmissionRepository:
    def __init__(self) -> None:
        # RU: Каждый экземпляр имеет собственный словарь.
        # EN: Each instance has its own dictionary.
        self._submissions: dict[str, Submission] = {}

    def get(self, submission_id: str) -> Submission | None:
        # RU: Возвращаем работу или None, если она не найдена.
        # EN: Return the submission or None if it is not found.
        return self._submissions.get(submission_id)

    def add(self, submission: Submission) -> None:
        # RU: Запрещаем замену работы с существующим идентификатором.
        # EN: Prevent replacing a submission with an existing identifier.
        if submission.submission_id in self._submissions:
            raise SubmissionError(
                code="conflict",
                field="submission_id",
                message=(
                    "Идентификатор уже существует / "
                    "The identifier already exists"
                ),
            )

        # RU: Сохраняем объект по его идентификатору.
        # EN: Store the object under its identifier.
        self._submissions[submission.submission_id] = submission
