# RU: Читаем JSON и проверяем дату и время.
# EN: Decode JSON and validate dates and times.
import json
from collections.abc import Iterable
from typing import Never
from datetime import datetime

# RU: Используем структурированные ошибки проекта.
# EN: Use the project's structured errors.
from school_lab.errors import SubmissionError

# RU: Создаём объекты из проверенных данных.
# EN: Create objects from validated data.
from school_lab.models import AIDeclaration, Submission


# RU: Поля, предусмотренные схемой сдачи.
# EN: Fields defined by the submission schema.
SUBMISSION_FIELDS = (
    "schema_version",
    "submission_id",
    "student_id",
    "assignment_id",
    "submitted_at",
    "text",
    "code",
    "template_id",
    "ai_declaration",
)


# RU: Поля декларации использования ИИ.
# EN: Fields of the AI usage declaration.
DECLARATION_FIELDS = (
    "used",
    "tool",
    "purpose",
    "verified_by_student",
)




# RU: Отклоняем повторяющиеся ключи JSON.
# EN: Reject repeated JSON keys.
def reject_repeated_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    # RU: Создаём словарь для проверенных пар.
    # EN: Create a dictionary for the checked pairs.
    result = {}

    # RU: Последовательно читаем ключ и значение каждой пары.
    # EN: Read the key and value of each pair in sequence.
    for key, value in pairs:
        # RU: Повторный ключ делает входные данные неоднозначными.
        # EN: A repeated key makes the input ambiguous.
        if key in result:
            raise SubmissionError(
                code="invalid_json",
                field=key,
                message="Повтор ключа запрещён / Repeated key is not allowed"
            )

        # RU: Сохраняем пару, если ключ ещё не встречался.
        # EN: Store the pair if the key has not appeared before.
        result[key] = value

    return result

# RU: Отклоняем специальные константы, запрещённые в JSON.
# EN: Reject special constants that are forbidden in JSON.
def reject_json_constant(value: str) -> Never:
    raise SubmissionError(
        code="invalid_json",
        field="json",
        message=(
            "Недопустимая константа JSON / "
            f"Invalid JSON constant: {value}"
        )
    )


def decode_json(text: str) -> object:
    try:
        # RU: Проверяем повторяющиеся ключи и специальные константы.
        # EN: Check repeated keys and special constants.
        return json.loads(
            text,
            object_pairs_hook = reject_repeated_keys,
            parse_constant = reject_json_constant
        )

    except json.JSONDecodeError as error:
        message = (
            f"Ошибка JSON / Invalid JSON: "
            f"line={error.lineno}, column={error.colno}"
        )

        raise SubmissionError(
            code="invalid_json",
            field="json",
            message=message
        ) from error

# RU: Проверяем версию схемы входных данных.
# EN: Validate the schema version of the input data.
def validate_schema_version(value: object) -> int:
    # RU: Требуется именно целое число, а не bool.
    # EN: Require an exact integer type, excluding bool.
    if type(value) is not int:
        raise SubmissionError(
            code="schema_error",
            field="schema_version",
            message="Ожидается целое число / An integer is required"
        )

    # RU: Программа поддерживает только версию 1.
    # EN: The program supports only version 1.
    if value != 1:
        raise SubmissionError(
            code="unsupported_version",
            field="schema_version",
            message="Поддерживается только версия 1 / Only version 1 is supported"
        )

    # RU: Возвращаем проверенную версию.
    # EN: Return the validated version.
    return value

# RU: Проверяем тип строки, затем её содержимое.
# EN: Check the string type, then its content.
def require_nonempty_string(value: object, field: str) -> str:
    # RU: Повторно используем общую проверку типа.
    # EN: Reuse the common type check.
    value = require_string(value, field)

    if value.strip() == "":
        raise SubmissionError(
            code="schema_error",
            field=field,
            message="Значение не должно быть пустым / The value must not be empty"
        )

    return value

# RU: Проверяем обязательные и неизвестные поля.
# EN: Check required and unknown fields.
def require_fields(data: dict[str, object], expected_fields: Iterable[str], prefix: str = "") -> None:
    # RU: Проверяем наличие каждого обязательного поля.
    # EN: Check that each required field is present.
    for field in expected_fields:
        if field not in data:
            full_field = prefix + field

            raise SubmissionError(
                code="schema_error",
                field=full_field,
                message=(
                    "Обязательное поле отсутствует / "
                    "Required field is missing"
                )
            )

    # RU: Отклоняем поля, которых нет в списке ожидаемых.
    # EN: Reject fields that are not in the expected field list.
    for field in data:
        if field not in expected_fields:
            full_field = prefix + field

            raise SubmissionError(
                code="schema_error",
                field=full_field,
                message="Неизвестное поле / Unknown field"
            )

# RU: Проверяем, что полученное значение является словарём.
# EN: Check that the received value is a dictionary.
def require_object(value: object, field: str) -> dict[str, object]:
    # RU: Отклоняем значения другого типа.
    # EN: Reject values of any other type.
    if not isinstance(value, dict):
        raise SubmissionError(
            code="schema_error",
            field=field,
            message="Ожидается JSON-объект / A JSON object is required"
        )

    # RU: Возвращаем исходный словарь без изменений.
    # EN: Return the original dictionary unchanged.
    return value

# RU: Проверяем, что значение является строкой.
# EN: Check that the value is a string.
def require_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise SubmissionError(
            code="schema_error",
            field=field,
            message="Ожидается строка / A string is required"
        )

    # RU: Возвращаем исходную строку, даже если она пустая.
    # EN: Return the original string, even if it is empty.
    return value

# RU: Разрешаем None или непустую строку.
# EN: Allow None or a non-empty string.
def optional_string(value: object, field: str) -> str | None:
    # RU: При отсутствии значения возвращаем None.
    # EN: Return None when no value is provided.
    if value is None:
        return None

    # RU: Иначе проверяем, что значение является непустой строкой.
    # EN: Otherwise, check that the value is a non-empty string.
    return require_nonempty_string(value, field)


# RU: Проверяем, что значение имеет тип bool.
# EN: Check that the value has the bool type.
def require_bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise SubmissionError(
            code="schema_error",
            field=field,
            message="Ожидается логическое значение / A boolean is required"
        )

    # RU: Возвращаем исходное логическое значение.
    # EN: Return the original boolean value.
    return value

# RU: Проверяем дату и время сдачи с часовым поясом.
# EN: Validate the submission timestamp and its time zone.
def validate_timestamp(value: object) -> str:
    # RU: Сначала проверяем, что получена непустая строка.
    # EN: First, check that the input is a non-empty string.
    value = require_nonempty_string(value, "submitted_at")

    try:
        # RU: Преобразуем строку в объект даты и времени.
        # EN: Parse the string into a datetime object.
        parsed = datetime.fromisoformat(value)

    except ValueError as error:
        # RU: Преобразуем ошибку даты в ошибку нашей схемы.
        # EN: Convert the date parsing error into our schema error.
        raise SubmissionError(
            code="schema_error",
            field="submitted_at",
            message="Некорректная дата или время / Invalid date or time"
        ) from error

    # RU: Требуем явно указанный часовой пояс.
    # EN: Require an explicitly specified time zone.
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SubmissionError(
            code="schema_error",
            field="submitted_at",
            message="Часовой пояс обязателен / A time zone is required"
        )

    # RU: Сохраняем исходное строковое представление.
    # EN: Preserve the original string representation.
    return value


# RU: Проверяем входные данные и создаём объект сдачи.
# EN: Validate input data and create a submission object.
def parse_submission(raw: object) -> Submission:
    # RU: Проверяем структуру и набор полей.
    # EN: Check the structure and the set of fields.
    data = require_object(raw, "submission")
    require_fields(data, SUBMISSION_FIELDS)

    # RU: Проверяем версию схемы.
    # EN: Validate the schema version.
    schema_version = validate_schema_version(data["schema_version"])

    # RU: Проверяем идентификаторы.
    # EN: Validate the identifiers.
    submission_id = require_nonempty_string(
        data["submission_id"], "submission_id"
    )
    student_id = require_nonempty_string(
        data["student_id"], "student_id"
    )
    assignment_id = require_nonempty_string(
        data["assignment_id"], "assignment_id"
    )

    # RU: Проверяем дату и время сдачи.
    # EN: Validate the submission timestamp.
    submitted_at = validate_timestamp(data["submitted_at"])

    # RU: Проверяем текст и исходный код.
    # EN: Validate the text and source code.
    text = require_string(data["text"], "text")
    source_code = require_string(data["code"], "code")

    if text.strip() == "" and source_code.strip() == "":
        raise SubmissionError(
            code="schema_error",
            field="text/code",
            message="Текст или код должны быть непустыми / Text or code must be non-empty"
        )

    # RU: Проверяем идентификатор шаблона.
    # EN: Validate the template identifier.
    template_id = optional_string(data["template_id"], "template_id")

    # RU: Проверяем структуру декларации ИИ.
    # EN: Validate the structure of the AI declaration.
    declaration = require_object(
        data["ai_declaration"], "ai_declaration"
    )

    # RU: Проверяем поля вложенной декларации ИИ.
    # EN: Validate the fields of the nested AI declaration.
    require_fields(
        declaration,
        DECLARATION_FIELDS,
        prefix="ai_declaration."
    )
    # RU: Проверяем значения полей декларации.
    # EN: Validate the declaration field values.
    ai_used = require_bool(
        declaration["used"], "ai_declaration.used"
    )
    verified_by_student = require_bool(
        declaration["verified_by_student"],
        "ai_declaration.verified_by_student"
    )
    ai_tool = optional_string(
        declaration["tool"], "ai_declaration.tool"
    )
    ai_purpose = optional_string(
        declaration["purpose"], "ai_declaration.purpose"
    )

    # RU: При использовании ИИ инструмент и цель обязательны.
    # EN: When AI is used, both the tool and purpose are required.
    if ai_used and (ai_tool is None or ai_purpose is None):
        raise SubmissionError(
            code="schema_error",
            field="ai_declaration",
            message="При использовании ИИ укажите инструмент и цель / When AI is used, provide the tool and purpose"
        )

    # RU: Создаём объект декларации из проверенных значений.
    # EN: Create the declaration object from validated values.
    ai_declaration = AIDeclaration(
        used=ai_used,
        tool=ai_tool,
        purpose=ai_purpose,
        verified_by_student=verified_by_student
    )

    # RU: Создаём и возвращаем проверенную сдачу.
    # EN: Create and return the validated submission.
    return Submission(
        schema_version=schema_version,
        submission_id=submission_id,
        student_id=student_id,
        assignment_id=assignment_id,
        submitted_at=submitted_at,
        text=text,
        code=source_code,
        template_id=template_id,
        ai_declaration=ai_declaration
    )
