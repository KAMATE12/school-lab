# RU: Импортируем средства копирования объектов.
# EN: Import the tools for copying objects.
import copy

from pathlib import Path

from school_lab.errors import SubmissionError
from school_lab.models import AIDeclaration, Submission

# RU: Используем чтение JSON и проверку данных из пакета.
# EN: Use JSON decoding and data validation from the package.
from school_lab.validation import decode_json, parse_submission

# RU: Используем преобразование данных и вычисление хеша из пакета.
# EN: Use data conversion and hash computation from the package.
from school_lab.serialization import (
    submission_to_dict,
    canonical_json,
    submission_hash,
)

# RU: Используем хранилище и сервис приёма из пакета.
# EN: Use the repository and acceptance service from the package.
from school_lab.repository import InMemorySubmissionRepository
from school_lab.service import accept_submission

# RU: Используем импорт JSONL из пакета.
# EN: Use JSONL importing from the package.
from school_lab.importing import import_json_lines


# RU: Сохраняем пример сдачи в формате JSON. 
# EN: Store a sample submission in JSON format."student_id":  
raw_submission = """
{
    "schema_version": 1,
    "submission_id": "sub-001",
    "student_id": "student-001",
    "assignment_id": "assignment-01",
    "submitted_at": "2026-10-10T17:00:00+00:00",
    "text": "Example solution.",
    "code": "print(2 + 3)",
    "template_id": null,
    "ai_declaration": {
        "used": false,
        "tool": null,
        "purpose": null,
        "verified_by_student": true
    }
}
"""

# RU: Преобразуем JSON-строку в словарь Python.
# EN: Convert the JSON string into a Python dictionary.


# RU: Выводим идентификаторы сдачи и студента.
# EN: Display the submission and student identifiers.
#print(submission["submission_id"])
#print(submission["student_id"])

# RU: Отобразить задание-01
# EN: Display the assignment-01
#print(submission["assignment_id"])



# RU: Запускаем учебные примеры.
# EN: Run the learning examples.
def run_experiments() -> None:

    try:
        # RU: Разбираем входной JSON.
        # EN: Decode the input JSON.
        raw_data = decode_json(raw_submission)

        # RU: Создаём независимую копию перед проверкой.
        # EN: Create an independent copy before validation.
        before_validation = copy.deepcopy(raw_data)

        # RU: Проверяем данные и создаём объект сдачи.
        # EN: Validate the data and create the submission object.
        validated_submission = parse_submission(raw_data)

        # RU: Сравниваем данные сразу после проверки.
        # EN: Compare the data immediately after validation.
        input_unchanged = raw_data == before_validation

        # RU: Останавливаем тест, если данные изменились.
        # EN: Stop the test if the data has changed.
        assert input_unchanged, "Input data was modified"

    except SubmissionError as error:
        print("Error code:", error.code)
        print("Field:", error.field)
        print("Message:", error.message)

    else:
        print("Validated submission:", validated_submission.submission_id)
        print("Student:", validated_submission.student_id)
        print("Assignment:", validated_submission.assignment_id)
        print("Submitted at:", validated_submission.submitted_at)
        print("AI used:", validated_submission.ai_declaration.used)
        print("Input unchanged:", input_unchanged)

        # RU: Получаем словарь из проверенного объекта.
        # EN: Obtain a dictionary from the validated object.
        submission_data = submission_to_dict(validated_submission)

        print("Converted type:", type(submission_data))
        print("Student from dictionary:", submission_data["student_id"])

        print(
            "Nested declaration type:",
            type(submission_data["ai_declaration"])
        )

        print(
            "AI used from dictionary:",
            submission_data["ai_declaration"]["used"]
        )

        print(
            "Same data as input:",
            submission_data == raw_data
        )

            # RU: Преобразуем словарь в канонический JSON.
        # EN: Convert the dictionary into canonical JSON.
        canonical_text = canonical_json(submission_data)

        print("Canonical type:", type(canonical_text))
        print("Canonical JSON:", canonical_text)

        # RU: Проверяем, что преобразование сохраняет данные.
        # EN: Check that the conversion preserves the data.
        restored_data = decode_json(canonical_text)

        print("Round trip preserved:", restored_data == submission_data)

            # RU: Создаём одинаковые данные с разным порядком ключей.
        # EN: Create equal data with different key orders.
        first = {"b": 2, "a": 1}
        second = {"a": 1, "b": 2}

        first_json = canonical_json(first)
        second_json = canonical_json(second)

        print("First canonical JSON:", first_json)
        print("Second canonical JSON:", second_json)
        print("Same canonical text:", first_json == second_json)

        # RU: Дважды вычисляем хеш одной и той же работы.
        # EN: Compute the hash of the same submission twice.
        first_hash = submission_hash(validated_submission)
        second_hash = submission_hash(validated_submission)

        print("Submission hash:", first_hash)
        print("Hash type:", type(first_hash))
        print("Hash length:", len(first_hash))
        print("Same submission, same hash:", first_hash == second_hash)

            # RU: Создаём независимую копию исходных данных.
        # EN: Create an independent copy of the input data.
        changed_data = copy.deepcopy(raw_data)

        # RU: Изменяем только код в копии.
        # EN: Change only the code in the copy.
        changed_data["code"] = validated_submission.code + "\n# test"

        # RU: Проверяем изменённые данные и создаём новый объект.
        # EN: Validate the changed data and create a new object.
        changed_submission = parse_submission(changed_data)

        changed_hash = submission_hash(changed_submission)

        print("Changed submission hash:", changed_hash)
        print("Changed code, different hash:", first_hash != changed_hash)
        print("Original input unchanged:", raw_data == before_validation)

            # RU: Создаём пустое хранилище для проверки сервиса.
        # EN: Create an empty repository to test the service.
        repository = InMemorySubmissionRepository()

        # RU: Первое поступление создаёт запись.
        # EN: The first submission creates a stored entry.
        accepted, is_duplicate = accept_submission(
            validated_submission,
            repository
        )

        print("First reception duplicate:", is_duplicate)
        print("First reception original:", accepted is validated_submission)

        # RU: Создаём другой объект с теми же данными.
        # EN: Create a different object containing the same data.
        repeated_submission = parse_submission(copy.deepcopy(raw_data))

        print(
            "Repeated object is original:",
            repeated_submission is validated_submission
        )

        # RU: Повторное поступление возвращает сохранённый объект.
        # EN: A repeated submission returns the stored object.
        accepted_again, is_duplicate_again = accept_submission(
            repeated_submission,
            repository
        )

        print("Second reception duplicate:", is_duplicate_again)
        print(
            "Second reception returns original:",
            accepted_again is validated_submission
        )

        # RU: Другие данные с тем же идентификатором вызывают конфликт.
        # EN: Different data with the same identifier cause a conflict.
        try:
            accept_submission(changed_submission, repository)
        except SubmissionError as error:
            print("Changed reception blocked:", error.code)

        print(
            "Original still stored:",
            repository.get(validated_submission.submission_id)
            is validated_submission
        )

            # RU: Создаём данные новой версии работы.
        # EN: Create the data for a new submission version.
        new_version_data = submission_to_dict(changed_submission)

        # RU: Назначаем новому поступлению отдельный идентификатор.
        # EN: Assign a separate identifier to the new submission.
        new_version_data["submission_id"] = "sub-002"

        # RU: Проверяем данные новой версии.
        # EN: Validate the new version data.
        new_version = parse_submission(new_version_data)

        # RU: Сохраняем новую версию в том же хранилище.
        # EN: Store the new version in the same repository.
        accepted_version, version_is_duplicate = accept_submission(
            new_version,
            repository
        )

        print("New version duplicate:", version_is_duplicate)
        print("New version ID:", accepted_version.submission_id)

        print(
            "Old version still stored:",
            repository.get("sub-001") is validated_submission
        )

        print(
            "New version stored:",
            repository.get("sub-002") is new_version
        )

        print(
            "Same student:",
            accepted_version.student_id == validated_submission.student_id
        )

        print(
            "Same assignment:",
            accepted_version.assignment_id
            == validated_submission.assignment_id
        )

            # RU: Используем новое хранилище для пакетной проверки.
        # EN: Use a fresh repository for the batch test.
        batch_repository = InMemorySubmissionRepository()

        # RU: Создаём пять строк с разными случаями.
        # EN: Create five lines covering different cases.
        json_lines = [
            canonical_json(submission_to_dict(validated_submission)),
            canonical_json(submission_to_dict(validated_submission)),
            '{"schema_version":',
            canonical_json(submission_to_dict(changed_submission)),
            canonical_json(submission_to_dict(new_version))
        ]

        # RU: Обрабатываем строки и выводим итог.
        # EN: Process the lines and display the summary.
        summary = import_json_lines(json_lines, batch_repository)

        print("Import summary:", summary)
        print(
            "Last submission stored:",
            batch_repository.get("sub-002") is not None
        )

        # RU: Создаём путь к тестовому файлу рядом со скриптом.
        # EN: Build the test file path next to the script.
        jsonl_path = Path(__file__).resolve().parent / "submissions_demo.jsonl"

        # RU: Записываем каждый JSON-текст на отдельной строке.
        # EN: Write each JSON text on a separate line.
        with jsonl_path.open("w", encoding="utf-8") as output_file:
            for json_line in json_lines:
                output_file.write(json_line + "\n")

        print("JSONL file:", jsonl_path)

            # RU: Используем отдельное хранилище для импорта из файла.
        # EN: Use a separate repository for the file import.
        file_repository = InMemorySubmissionRepository()

        # RU: Читаем файл построчно и обрабатываем работы.
        # EN: Read the file line by line and process submissions.
        with jsonl_path.open("r", encoding="utf-8") as input_file:
            file_summary = import_json_lines(
                input_file,
                file_repository
            )

        print("File import summary:", file_summary)
        print("Input file closed:", input_file.closed)

        print(
            "Last submission stored from file:",
            file_repository.get("sub-002") is not None
        )


    print("Validation step finished.")

if __name__ == "__main__":
    run_experiments()
