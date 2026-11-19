from collections.abc import Iterable, Iterator

from school_lab.corpus_pairs import (
    PreparedSubmission,
    iter_eligible_pairs,
)
from school_lab.errors import SubmissionError
from school_lab.pair_comparison import TokenComparison
from school_lab.similarity import jaccard_similarity


# RU: Сравниваем уже подготовленные работы без повторного разбора кода.
# EN: Compare prepared submissions without parsing their code again.
def compare_prepared_submissions(
    first: PreparedSubmission,
    second: PreparedSubmission,
) -> TokenComparison:
    # RU: Проверяем допустимость пары при прямом вызове функции.
    # EN: Check pair eligibility when the function is called directly.
    if first.submission.submission_id == second.submission.submission_id:
        raise SubmissionError(
            code="self_match",
            field="submission_id",
            message="Самосравнение запрещено / Self-match is not allowed",
        )

    if first.submission.assignment_id != second.submission.assignment_id:
        raise SubmissionError(
            code="assignment_mismatch",
            field="assignment_id",
            message="Разные задания / Different assignments",
        )

    if first.submission.student_id == second.submission.student_id:
        raise SubmissionError(
            code="same_student",
            field="student_id",
            message="Один и тот же студент / The same student",
        )

    left = first.features
    right = second.features

    # RU: Не смешиваем признаки с разными разрешёнными шаблонами.
    # EN: Do not mix features prepared with different allowed templates.
    if left.allowed_template != right.allowed_template:
        raise SubmissionError(
            code="configuration_mismatch",
            field="allowed_template",
            message=(
                "Разные конфигурации шаблона / "
                "Different template configurations"
            ),
        )

    # RU: Используем готовые множества признаков.
    # EN: Use the existing feature sets.
    score = jaccard_similarity(left.keys, right.keys)
    common_keys = left.keys & right.keys

    return TokenComparison(
        first_id=first.submission.submission_id,
        second_id=second.submission.submission_id,
        score=score,
        first_matches=tuple(
            item for item in left.occurrences
            if item.key in common_keys
        ),
        second_matches=tuple(
            item for item in right.occurrences
            if item.key in common_keys
        ),
        first_template_lines=left.template_lines,
        second_template_lines=right.template_lines,
    )


# RU: Выдаём результаты допустимых пар последовательно.
# EN: Yield eligible pair results sequentially.
def iter_token_comparisons(
    prepared: Iterable[PreparedSubmission],
) -> Iterator[TokenComparison]:
    for first, second in iter_eligible_pairs(prepared):
        yield compare_prepared_submissions(first, second)