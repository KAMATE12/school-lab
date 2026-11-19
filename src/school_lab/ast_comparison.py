from dataclasses import dataclass

from school_lab.ast_features import AstOccurrence, PreparedAstCode
from school_lab.errors import SubmissionError
from school_lab.models import Submission
from school_lab.serialization import submission_hash


# RU: Связываем проверенную работу с готовыми AST-признаками.
# EN: Associate a validated submission with prepared AST features.
@dataclass(frozen=True)
class PreparedAstSubmission:
    submission: Submission
    features: PreparedAstCode


@dataclass(frozen=True)
class AstComparison:
    first_id: str
    second_id: str
    first_hash: str
    second_hash: str
    score: float | None
    first_matches: tuple[AstOccurrence, ...]
    second_matches: tuple[AstOccurrence, ...]
    first_template_lines: tuple[int, ...]
    second_template_lines: tuple[int, ...]
    config_hash: str
    method_version: str
    method: str = "ast_statement_jaccard"


# RU: Сравниваем готовые структуры без повторного разбора Python.
# EN: Compare prepared structures without parsing Python again.
def compare_ast_submissions(
    first: PreparedAstSubmission,
    second: PreparedAstSubmission,
) -> AstComparison:
    left, right = first.submission, second.submission
    for invalid, code, field in (
        (left.submission_id == right.submission_id, "self_match", "submission_id"),
        (left.assignment_id != right.assignment_id, "assignment_mismatch", "assignment_id"),
        (left.student_id == right.student_id, "same_student", "student_id"),
        (first.features.config_hash != second.features.config_hash
         or first.features.method_version != second.features.method_version,
         "configuration_mismatch", "config_hash"),
    ):
        if invalid:
            raise SubmissionError(
                code=code, field=field,
                message="Недопустимая пара / Ineligible pair: " + code,
            )
    a, b = first.features, second.features
    union = a.keys | b.keys
    common = a.keys & b.keys
    # RU: Пустое объединение означает недостаток данных, а не нулевое сходство.
    # EN: An empty union means insufficient data, not zero similarity.
    score = len(common) / len(union) if union else None
    return AstComparison(
        left.submission_id, right.submission_id,
        submission_hash(left), submission_hash(right), score,
        tuple(item for item in a.occurrences if item.key in common),
        tuple(item for item in b.occurrences if item.key in common),
        a.template_lines, b.template_lines, a.config_hash, a.method_version,
    )
