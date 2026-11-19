"""Sequential AST corpus comparison; this command never executes submitted code."""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from school_lab.assignments import parse_assignments
from school_lab.ast_comparison import PreparedAstSubmission, compare_ast_submissions
from school_lab.ast_features import prepare_ast_code
from school_lab.errors import SubmissionError
from school_lab.pipeline import iter_validated_submissions
from school_lab.repository import InMemorySubmissionRepository
from school_lab.service import accept_submission


# RU: Читаем JSONL построчно и сохраняем каждую допустимую пару один раз.
# EN: Read JSONL line by line and save each eligible pair once.
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Сравнение AST / AST comparison")
    parser.add_argument("path", type=Path)
    parser.add_argument("--assignments", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    stats = dict(accepted=0, prepared=0, duplicate=0, errors=0,
                 comparisons=0, insufficient=0)
    repository = InMemorySubmissionRepository()
    by_assignment = {}
    try:
        assignments = parse_assignments(json.loads(args.assignments.read_text(encoding="utf-8")))
        # RU: Режим x защищает существующий файл результатов.
        # EN: Mode x protects an existing results file.
        with args.path.open(encoding="utf-8") as lines:
            with args.output.open("x", encoding="utf-8") as output:
                for result in iter_validated_submissions(lines):
                    try:
                        if result.error is not None:
                            raise result.error
                        if result.submission is None:
                            raise RuntimeError("Missing validated submission")
                        submission, duplicate = accept_submission(result.submission, repository)
                        if duplicate:
                            stats["duplicate"] += 1
                            continue
                        stats["accepted"] += 1
                        assignment = assignments.get(submission.assignment_id)
                        if assignment is None:
                            raise SubmissionError(
                                code="unknown_assignment", field="assignment_id",
                                message="Неизвестное задание / Unknown assignment",
                            )
                        features = prepare_ast_code(submission.code, assignment.allowed_template)
                        current = PreparedAstSubmission(submission, features)
                    except SubmissionError as error:
                        stats["errors"] += 1
                        print(f"Line {result.line_number}: {error.code}, field={error.field}: {error.message}",
                              file=sys.stderr)
                        continue
                    stats["prepared"] += 1
                    previous = by_assignment.setdefault(submission.assignment_id, [])
                    for other in previous:
                        if other.submission.student_id == submission.student_id:
                            continue
                        comparison = compare_ast_submissions(other, current)
                        output.write(json.dumps(asdict(comparison), ensure_ascii=False,
                                                sort_keys=True, allow_nan=False) + "\n")
                        stats["comparisons"] += 1
                        stats["insufficient"] += comparison.score is None
                    previous.append(current)
    except (OSError, UnicodeError, ValueError, SubmissionError) as error:
        print(f"Ошибка файла или конфигурации / File or configuration error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(stats, sort_keys=True))
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
