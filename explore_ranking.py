import json
from pathlib import Path

from school_lab.assignments import parse_assignments
from school_lab.ast_comparison import PreparedAstSubmission
from school_lab.ast_features import prepare_ast_code
from school_lab.corpus_import import CorpusImportStats, iter_imported_prepared
from school_lab.errors import SubmissionError
from school_lab.ranking import rank_ast_candidates, rank_token_candidates
from school_lab.sources import JsonlFileSource


def show_error(line_number, error):
    print(f"Line {line_number}: {error.code}, field={error.field}")


def display(method, ranking):
    print(f"\n{method} top 3:")
    for match in ranking.matches:
        print(f"  {match.candidate_id}: score={match.score:.6f}")
    print(f"Compared={ranking.compared}; excluded={ranking.excluded}; "
          f"insufficient={ranking.insufficient}")


def main():
    root = Path(__file__).resolve().parent
    assignments = parse_assignments(json.loads(
        (root / "assignments.json").read_text(encoding="utf-8")
    ))
    templates = {key: value.allowed_template for key, value in assignments.items()}
    stats = CorpusImportStats()
    source = JsonlFileSource(root / "submissions.jsonl")

    # RU: Для небольшого примера сохраняем индекс подготовленных работ.
    # EN: Keep an index of prepared submissions for this small example.
    with source.open() as lines:
        token_corpus = list(iter_imported_prepared(lines, templates, stats, show_error))

    # RU: Подготавливаем второй метод один раз для каждой работы.
    # EN: Prepare the second method once for each submission.
    ast_corpus = []
    for item in token_corpus:
        submission = item.submission
        try:
            features = prepare_ast_code(submission.code, templates[submission.assignment_id])
        except SubmissionError as error:
            print(f"AST preparation: {submission.submission_id}: {error.code}")
            continue
        ast_corpus.append(PreparedAstSubmission(submission, features))

    # RU: Находим работу, для которой ищем похожие решения.
    # EN: Find the submission whose similar candidates we want to retrieve.
    token_query = next(item for item in token_corpus if item.submission.submission_id == "sub-001")
    ast_query = next(item for item in ast_corpus if item.submission.submission_id == "sub-001")

    display("Tokens", rank_token_candidates(token_query, token_corpus, k=3))
    display("AST", rank_ast_candidates(ast_query, ast_corpus, k=3))


if __name__ == "__main__":
    main()
