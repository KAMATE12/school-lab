# RU: Читаем аргументы, преобразуем отчёты и работаем с файлами.
# EN: Read arguments, convert reports, and work with files.
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from school_lab.analysis_service import (
    ANALYZER_FACTORIES,
    analyze_submission,
)
from school_lab.errors import SubmissionError
from school_lab.assignments import parse_assignments
from school_lab.models import AnalysisContext, Assignment
from school_lab.repository import InMemorySubmissionRepository
from school_lab.serialization import canonical_json
from school_lab.service import accept_submission
from school_lab.sources import JsonlFileSource
from school_lab.validation import decode_json, parse_submission


# RU: Анализируем работы и сохраняем отчёты в JSONL.
# EN: Analyze submissions and save reports as JSONL.
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Анализ работ / Analyze submissions"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Входной JSONL / Input JSONL",
    )
    parser.add_argument(
        "--assignment-id",
        required=True,
        help="Идентификатор задания / Assignment identifier",
    )
    parser.add_argument(
        "--analyzer",
        action="append",
        choices=sorted(ANALYZER_FACTORIES),
        required=True,
        help="Анализатор; можно повторять / Analyzer; may be repeated",
    )
    parser.add_argument(
        "--template-file",
        type=Path,
        help="Разрешённый шаблон UTF-8 / Allowed UTF-8 template",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Новый файл отчётов JSONL / New JSONL report file",
    )
    # RU: Необязательный каталог заданий содержит шаблон и требования.
    # EN: The optional assignment catalog contains templates and requirements.
    parser.add_argument("--assignments", type=Path, help="Каталог заданий JSON / Assignment JSON catalog")
    args = parser.parse_args()
    if args.assignments is not None and args.template_file is not None:
        parser.error("Use --assignments or --template-file, not both")

    # RU: Для анализа шаблона требуется его файл.
    # EN: Template analysis requires the template file.
    if "template" in args.analyzer and args.template_file is None and args.assignments is None:
        parser.error(
            "--template-file обязателен для template / "
            "--template-file is required for template"
        )

    # RU: Убираем повторные имена, сохраняя порядок выбора.
    # EN: Remove repeated names while preserving selection order.
    analyzer_ids = list(dict.fromkeys(args.analyzer))

    repository = InMemorySubmissionRepository()
    counts = {
        "accepted": 0,
        "duplicate": 0,
        "reports": 0,
        "errors": 0,
    }

    try:
        # RU: Читаем шаблон, если пользователь его указал.
        # EN: Read the template if the user supplied one.
        template = ""
        if args.template_file is not None:
            template = args.template_file.read_text(encoding="utf-8")

        assignment = Assignment(
            assignment_id=args.assignment_id,
            allowed_template=template,
            requirements=(),
        )
        if args.assignments is not None:
            catalog = parse_assignments(decode_json(args.assignments.read_text(encoding="utf-8")))
            if args.assignment_id not in catalog:
                raise SubmissionError("schema_error", "assignment_id", "Неизвестное задание / Unknown assignment")
            assignment = catalog[args.assignment_id]
        context = AnalysisContext(assignment=assignment)
        source = JsonlFileSource(args.path)

        # RU: Открываем вход и создаём новый файл отчётов.
        # EN: Open the input and create a new report file.
        with source.open() as lines:
            with args.output.open("x", encoding="utf-8") as output:
                for line_number, line in enumerate(lines, start=1):
                    try:
                        raw = decode_json(line)
                        submission = parse_submission(raw)

                        # RU: Проверяем задание до сохранения работы.
                        # EN: Check the assignment before storing the submission.
                        if submission.assignment_id != assignment.assignment_id:
                            raise SubmissionError(
                                code="assignment_mismatch",
                                field="assignment_id",
                                message=(
                                    "Работа относится к другому заданию / "
                                    "The submission belongs to another assignment"
                                ),
                            )

                        stored, is_duplicate = accept_submission(
                            submission,
                            repository,
                        )

                    except SubmissionError as error:
                        counts["errors"] += 1
                        print(
                            f"Line {line_number}: {error.code}, "
                            f"field={error.field}: {error.message}",
                            file=sys.stderr,
                        )
                        continue

                    if is_duplicate:
                        counts["duplicate"] += 1
                        continue

                    counts["accepted"] += 1

                    # RU: Ошибка одного анализатора не останавливает остальные.
                    # EN: One analyzer's failure does not stop the others.
                    for analyzer_id in analyzer_ids:
                        try:
                            report = analyze_submission(
                                stored,
                                context,
                                analyzer_id,
                            )
                        except SubmissionError as error:
                            counts["errors"] += 1
                            print(
                                f"Line {line_number}, analyzer={analyzer_id}: "
                                f"{error.code}, field={error.field}: "
                                f"{error.message}",
                                file=sys.stderr,
                            )
                            continue

                        # RU: Записываем каждый отчёт отдельной строкой.
                        # EN: Write each report on a separate line.
                        output.write(canonical_json(asdict(report)) + "\n")
                        counts["reports"] += 1

    except SubmissionError as error:
        print(f"{error.code}, field={error.field}: {error.message}", file=sys.stderr)
        return 2

    except (OSError, UnicodeError) as error:
        # RU: Сообщаем об ошибке чтения или записи файла.
        # EN: Report a file-reading or file-writing error.
        print(
            f"Ошибка файла / File error: {error}",
            file=sys.stderr,
        )
        return 2

    print(
        f"Summary: accepted={counts['accepted']}, "
        f"duplicate={counts['duplicate']}, "
        f"reports={counts['reports']}, "
        f"errors={counts['errors']}"
    )

    if counts["errors"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
