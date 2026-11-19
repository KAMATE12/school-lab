from dataclasses import dataclass

from school_lab.errors import SubmissionError
from school_lab.models import Submission
from school_lab.similarity import jaccard_similarity
# RU: Используем подготовку признаков и тип исходных позиций.
# EN: Use feature preparation and the occurrence type.
from school_lab.prepared_code import prepare_token_code
from school_lab.token_evidence import TrigramOccurrence


# RU: Храним результат сравнения и основания для объяснения.
# EN: Store the comparison result and supporting evidence.
@dataclass(frozen=True)
class TokenComparison:
    first_id: str
    second_id: str
    score: float | None
    first_matches: tuple[TrigramOccurrence, ...]
    second_matches: tuple[TrigramOccurrence, ...]
    first_template_lines: tuple[int, ...]
    second_template_lines: tuple[int, ...]


# RU: Сравниваем код двух проверенных работ.
# EN: Compare the code of two validated submissions.
def compare_token_submissions(
    first: Submission,
    second: Submission,
    allowed_template: str = "",
) -> TokenComparison:
    # RU: Запрещаем сравнение работы с самой собой.
    # EN: Reject comparison of a submission with itself.
    if first.submission_id == second.submission_id:
        raise SubmissionError(
            code="self_match",
            field="submission_id",
            message=(
                "Нельзя сравнивать работу с самой собой / "
                "Cannot compare a submission with itself"
            ),
        )

    # RU: Сравниваем только работы одного задания.
    # EN: Compare submissions from the same assignment only.
    if first.assignment_id != second.assignment_id:
        raise SubmissionError(
            code="assignment_mismatch",
            field="assignment_id",
            message=(
                "Работы относятся к разным заданиям / "
                "Submissions belong to different assignments"
            ),
        )

        # RU: Исключаем пары работ одного студента.
    # EN: Exclude pairs belonging to the same student.
    if first.student_id == second.student_id:
        raise SubmissionError(
            code="same_student",
            field="student_id",
            message=(
                "Работы принадлежат одному студенту / "
                "Submissions belong to the same student"
            ),
        )

    # RU: Подготавливаем признаки каждого исходного текста.
    # EN: Prepare the features of each source text.
    first_prepared = prepare_token_code(first.code, allowed_template)
    second_prepared = prepare_token_code(second.code, allowed_template)


    score = jaccard_similarity(
        first_prepared.keys,
        second_prepared.keys,
    )
    common_keys = first_prepared.keys & second_prepared.keys

    # RU: Сохраняем исходные позиции общих признаков.
    # EN: Preserve the original positions of shared features.
    first_matches = tuple(
        item for item in first_prepared.occurrences
        if item.key in common_keys
    )
    second_matches = tuple(
        item for item in second_prepared.occurrences
        if item.key in common_keys
    )

    return TokenComparison(
        first_id=first.submission_id,
        second_id=second.submission_id,
        score=score,
        first_matches=first_matches,
        second_matches=second_matches,
        first_template_lines=first_prepared.template_lines,
        second_template_lines=second_prepared.template_lines,
    )