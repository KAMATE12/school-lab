from collections.abc import Iterable
from dataclasses import dataclass

from school_lab.ast_comparison import (
    AstComparison, PreparedAstSubmission, compare_ast_submissions,
)
from school_lab.corpus_comparison import compare_prepared_submissions
from school_lab.corpus_pairs import PreparedSubmission
from school_lab.errors import SubmissionError
from school_lab.pair_comparison import TokenComparison


# RU: Храним кандидата, его оценку и исходные основания сравнения.
# EN: Store a candidate, its score, and the original comparison evidence.
@dataclass(frozen=True)
class RankedMatch:
    candidate_id: str
    score: float
    comparison: TokenComparison | AstComparison


# RU: Отделяем выбранные результаты от счётчиков обработки.
# EN: Separate selected results from processing counters.
@dataclass(frozen=True)
class RankingResult:
    matches: tuple[RankedMatch, ...]
    compared: int
    excluded: int
    insufficient: int


# RU: Общие правила отбора одинаковы для обеих методов.
# EN: Both methods share the same selection rules.
def _rank(query, candidates, compare, k: int) -> RankingResult:
    # RU: bool не принимается как целое число параметра k.
    # EN: A bool is not accepted as the integer parameter k.
    if type(k) is not int:
        raise TypeError("k должен быть целым числом / k must be an integer")
    if k < 1:
        raise ValueError("k должен быть положительным / k must be positive")

    matches = []
    seen_ids = set()
    compared = excluded = insufficient = 0
    source = query.submission

    for candidate in candidates:
        target = candidate.submission
        # RU: Корпус на этом этапе уже должен быть очищен от дубликатов.
        # EN: Duplicates must already have been resolved at this stage.
        if target.submission_id in seen_ids:
            raise SubmissionError(
                code="duplicate_input", field="submission_id",
                message="Повтор идентификатора / Repeated submission ID",
            )
        seen_ids.add(target.submission_id)

        # RU: Исключаем недопустимые пары до вычисления оценки.
        # EN: Exclude ineligible pairs before computing a score.
        if (source.submission_id == target.submission_id
                or source.assignment_id != target.assignment_id
                or source.student_id == target.student_id):
            excluded += 1
            continue

        comparison = compare(query, candidate)
        compared += 1
        # RU: Недостаток данных не превращаем в нулевую оценку.
        # EN: Do not turn insufficient data into a zero score.
        if comparison.score is None:
            insufficient += 1
            continue
        matches.append(RankedMatch(
            target.submission_id, comparison.score, comparison,
        ))

    # RU: Сначала большие оценки; при равенстве сортируем по идентификатору.
    # EN: Put higher scores first; break ties by submission ID.
    matches.sort(key=lambda match: (-match.score, match.candidate_id))
    return RankingResult(tuple(matches[:k]), compared, excluded, insufficient)


# RU: Выбираем кандидатов по токеновому сходству.
# EN: Select candidates by token similarity.
def rank_token_candidates(
    query: PreparedSubmission,
    candidates: Iterable[PreparedSubmission],
    k: int = 5,
) -> RankingResult:
    return _rank(query, candidates, compare_prepared_submissions, k)


# RU: Выбираем кандидатов по структурному сходству AST.
# EN: Select candidates by AST structural similarity.
def rank_ast_candidates(
    query: PreparedAstSubmission,
    candidates: Iterable[PreparedAstSubmission],
    k: int = 5,
) -> RankingResult:
    return _rank(query, candidates, compare_ast_submissions, k)
