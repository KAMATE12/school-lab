from dataclasses import dataclass
# RU: Ограничиваем допустимые значения некоторых полей в аннотациях.
# EN: Restrict the allowed values of some fields in type annotations.
from typing import Literal


# RU: Представляем декларацию использования ИИ.
# EN: Represent the AI usage declaration.
@dataclass(frozen=True)
class AIDeclaration:
    used: bool
    tool: str | None
    purpose: str | None
    verified_by_student: bool


# RU: Представляем проверенную отправленную работу.
# EN: Represent a validated submission.
@dataclass(frozen=True)
class Submission:
    schema_version: int
    submission_id: str
    student_id: str
    assignment_id: str
    submitted_at: str
    text: str
    code: str
    template_id: str | None
    ai_declaration: AIDeclaration

# RU: Описываем задание преподавателя.
# EN: Describe the teacher's assignment.
@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    allowed_template: str
    requirements: tuple[str, ...]


# RU: Передаём анализатору задание и доступные работы.
# EN: Provide the analyzer with the assignment and available submissions.
@dataclass(frozen=True)
class AnalysisContext:
    assignment: Assignment
    submissions: tuple[Submission, ...] = ()


# RU: Указываем строки исходной работы, подтверждающие наблюдение.
# EN: Identify original submission lines supporting a finding.
@dataclass(frozen=True)
class Evidence:
    submission_id: str
    field: Literal["text", "code"]
    start_line: int
    end_line: int


# RU: Представляем отдельное наблюдение анализатора.
# EN: Represent an individual analyzer finding.
@dataclass(frozen=True)
class Finding:
    kind: Literal[
        "similarity",
        "rubric_feedback",
        "processing_error",
    ]
    score: float | None
    evidence: tuple[Evidence, ...]
    explanation: str


# RU: Сохраняем результат анализа и сведения о его происхождении.
# EN: Store the analysis result and information about its origin.
@dataclass(frozen=True)
class AnalysisReport:
    report_id: str
    submission_id: str
    submission_hash: str
    analyzer_id: str
    analyzer_version: str
    config_hash: str
    findings: tuple[Finding, ...]
    created_at: str
    review_required: bool
