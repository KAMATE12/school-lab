import argparse
import sys
from pathlib import Path

# RU: Создаём хранилище с помощью класса из пакета.
# EN: Create the repository using the package class.
from school_lab.repository import InMemorySubmissionRepository

# RU: Импортируем строки с помощью компонента пакета.
# EN: Import lines using the package component.
from school_lab.importing import import_json_lines

# RU: Используем файловый источник строк.
# EN: Use the file-backed line source.
from school_lab.sources import JsonlFileSource

# RU: Отделяем диагностические сообщения от итогового JSON.
# EN: Separate diagnostic messages from the final JSON.
from contextlib import redirect_stdout

# RU: Формируем итоговый JSON с правилами проекта.
# EN: Format the final JSON using the project's rules.
from school_lab.serialization import canonical_json


# RU: Читаем аргументы командной строки и импортируем файл.
# EN: Read command-line arguments and import the file.
def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Импорт работ из JSONL / "
            "Import submissions from JSONL"
        )
    )

    # RU: Пользователь должен указать путь к файлу.
    # EN: The user must provide the file path.
    parser.add_argument(
        "path",
        type=Path,
        help="Путь к файлу JSONL / Path to the JSONL file",
    )

    args = parser.parse_args()

    # RU: Каждый запуск использует новое хранилище в памяти.
    # EN: Each run uses a new in-memory repository.
    repository = InMemorySubmissionRepository()

    try:
        # RU: Создаём источник и импортируем предоставленные строки.
        # EN: Create the source and import the provided lines.
        source = JsonlFileSource(args.path)

        # RU: Читаем источник и направляем сообщения в stderr.
        # EN: Read the source and direct diagnostic messages to stderr.
        with source.open() as lines:
            with redirect_stdout(sys.stderr):
                summary = import_json_lines(lines, repository)

    except (OSError, UnicodeError) as error:
        # RU: Сообщаем об ошибке чтения файла.
        # EN: Report a file-reading error.
        print(
            f"Ошибка чтения файла / File reading error: {error}",
            file=sys.stderr,
        )
        return 2

    # RU: Выводим единственный итоговый JSON в stdout.
    # EN: Write one final JSON summary to stdout.
    print(canonical_json(summary))

    # RU: Возвращаем код завершения по результатам импорта.
    # EN: Return an exit code based on the import results.
    if summary["errors"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
