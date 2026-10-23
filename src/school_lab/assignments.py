# RU: Проверяем каталог заданий из внешнего JSON.
# EN: Validate the assignment catalog from external JSON.
from school_lab.errors import SubmissionError
from school_lab.models import Assignment
from school_lab.validation import require_object, require_fields, require_string, require_nonempty_string


def parse_assignments(raw: object) -> dict[str, Assignment]:
    # RU: Формат каталога: массив объектов заданий.
    # EN: Catalog format: an array of assignment objects.
    if not isinstance(raw, list):
        raise SubmissionError("schema_error", "assignments", "Ожидается массив / An array is required")
    result: dict[str, Assignment] = {}
    for index, value in enumerate(raw):
        prefix = f"assignments[{index}]."
        data = require_object(value, prefix[:-1])
        require_fields(data, ("assignment_id", "allowed_template", "requirements"), prefix)
        identifier = require_nonempty_string(data["assignment_id"], prefix + "assignment_id")
        template = require_string(data["allowed_template"], prefix + "allowed_template")
        requirements = data["requirements"]
        if not isinstance(requirements, list):
            raise SubmissionError("schema_error", prefix + "requirements", "Ожидается массив / An array is required")
        checked = tuple(require_nonempty_string(item, prefix + "requirements") for item in requirements)
        if identifier in result:
            raise SubmissionError("conflict", prefix + "assignment_id", "Повтор задания / Repeated assignment")
        result[identifier] = Assignment(identifier, template, checked)
    return result
