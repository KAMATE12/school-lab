# RU: Используем модели задания, контекста и наблюдений.
# EN: Use assignment, context, and finding models.
from school_lab.models import (
    AnalysisContext,
    Assignment,
    Evidence,
    Finding,
)


# RU: Показываем, как связаны объекты анализа.
# EN: Demonstrate how analysis objects are connected.
def main() -> None:
    # RU: Описываем задание без разрешённого шаблона.
    # EN: Describe an assignment without an allowed template.
    assignment = Assignment(
        assignment_id="assignment-01",
        allowed_template="",
        requirements=(
            "Explain the solution.",
            "Provide Python code.",
        ),
    )

    # RU: Создаём контекст с пустым набором дополнительных работ.
    # EN: Create a context with no additional submissions.
    context = AnalysisContext(assignment=assignment)

    # RU: Ссылаемся на первую строку кода примера.
    # EN: Refer to the first code line of the example.
    evidence = Evidence(
        submission_id="sub-001",
        field="code",
        start_line=1,
        end_line=1,
    )

    # RU: Вручную создаём пример наблюдения без оценки.
    # EN: Manually create an example finding without a score.
    finding = Finding(
        kind="rubric_feedback",
        score=None,
        evidence=(evidence,),
        explanation=(
            "Пример содержит строку кода / "
            "The example contains a line of code"
        ),
    )

    print("Assignment:", context.assignment.assignment_id)
    print("Requirements:", len(context.assignment.requirements))
    print("Context submissions:", len(context.submissions))
    print("Finding kind:", finding.kind)
    print("Finding score:", finding.score)
    print("Evidence field:", finding.evidence[0].field)
    print("Evidence start line:", finding.evidence[0].start_line)


if __name__ == "__main__":
    main()
