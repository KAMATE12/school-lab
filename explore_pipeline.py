from pathlib import Path

from school_lab.pipeline import iter_validated_submissions
from school_lab.sources import JsonlFileSource


def main() -> None:
    # RU: Находим входной файл рядом со скриптом.
    # EN: Locate the input file beside the script.
    path = Path(__file__).resolve().parent / "submissions_demo.jsonl"
    source = JsonlFileSource(path)

    # RU: Закрываем файл при выходе из блока with.
    # EN: Close the file when leaving the with block.
    with source.open() as lines:
        results = iter_validated_submissions(lines)

        # RU: Запрашиваем результаты по одному.
        # EN: Request results one at a time.
        for result in results:
            if result.error is not None:
                print(
                    f"Line {result.line_number}: "
                    f"error={result.error.code}"
                )
            else:
                print(
                    f"Line {result.line_number}: "
                    f"valid id={result.submission.submission_id}"
                )


# RU: Запускаем пример при прямом выполнении файла.
# EN: Run the example when the file is executed directly.
if __name__ == "__main__":
    main()
