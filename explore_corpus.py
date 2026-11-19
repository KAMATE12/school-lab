import json
from dataclasses import asdict
from pathlib import Path

from school_lab.assignments import parse_assignments
from school_lab.corpus_comparison import iter_token_comparisons
from school_lab.corpus_import import (
    CorpusImportStats,
    iter_imported_prepared,
)
from school_lab.errors import SubmissionError
from school_lab.sources import JsonlFileSource


# RU: Показываем структурированную ошибку.
# EN: Display a structured error.
def show_error(line_number: int, error: SubmissionError) -> None:
    print(
        f"Line {line_number}: "
        f"error={error.code}, field={error.field}"
    )
    print("Message:", error.message)


def main() -> None:
    root = Path(__file__).resolve().parent

    catalog_data = json.loads(
        (root / "assignments.json").read_text(encoding="utf-8")
    )
    assignments = parse_assignments(catalog_data)

    templates = {
        assignment_id: assignment.allowed_template
        for assignment_id, assignment in assignments.items()
    }

    source = JsonlFileSource(root / "submissions.jsonl")
    output_path = root / "token_comparisons_demo.jsonl"

    stats = CorpusImportStats()
    pair_count = 0
    insufficient_count = 0

    # RU: Создаём новый файл, не перезаписывая существующий.
    # EN: Create a new file without overwriting an existing one.
    with output_path.open("x", encoding="utf-8") as output:
        # RU: Закрываем входной файл после обработки.
        # EN: Close the input file after processing.
        with source.open() as lines:
            prepared = iter_imported_prepared(
                lines,
                templates,
                stats,
                show_error,
            )

            for comparison in iter_token_comparisons(prepared):
                pair_count += 1

                if comparison.score is None:
                    insufficient_count += 1

                # RU: Преобразуем результат и позиции в обычные данные.
                # EN: Convert the result and positions to ordinary data.
                record = asdict(comparison)

                # RU: Сохраняем один JSON-объект на физическую строку.
                # EN: Save one JSON object per physical line.
                output.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        sort_keys=True,
                        allow_nan=False,
                    )
                    + "\n"
                )

    print("Import summary:", asdict(stats))
    print("Compared pairs:", pair_count)
    print("Insufficient-data pairs:", insufficient_count)
    print("Results file:", output_path)


if __name__ == "__main__":
    main()