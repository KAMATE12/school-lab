"""Fixed-pair evaluation: tune first, evaluate only with a frozen policy."""
import argparse
import hashlib
import json
import platform
import sys
from dataclasses import asdict
from pathlib import Path

from school_lab.assignments import parse_assignments
from school_lab.ast_comparison import PreparedAstSubmission, compare_ast_submissions
from school_lab.ast_features import AST_VERSION, prepare_ast_code
from school_lab.corpus_comparison import compare_prepared_submissions
from school_lab.corpus_pairs import PreparedSubmission
from school_lab.errors import SubmissionError
from school_lab.prepared_code import prepare_token_code
from school_lab.quality_corpus import validate_quality_data
from school_lab.serialization import submission_hash
from school_lab.validation import decode_json, parse_submission

METHODS = ("token", "ast")
POLICY = "max F1 on defined tuning scores; ties: precision, then larger threshold"
VERSION = "quality-experiment-1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


# RU: Читаем строки по одной и проверяем зафиксированные хеши файлов.
# EN: Read one line at a time and verify the recorded file hashes.
def load_corpus(directory):
    directory = Path(directory)
    manifest_bytes = (directory / "manifest.json").read_bytes()
    manifest = decode_json(manifest_bytes.decode("utf-8"))
    for name in ("submissions.jsonl", "provenance.jsonl", "pairs.jsonl", "assignments.json", ".gitattributes"):
        if digest((directory / name).read_bytes()) != manifest["sha256"][name]:
            raise ValueError("Corpus hash mismatch: " + name)
    data = {}
    for name in ("submissions", "provenance", "pairs"):
        with (directory / (name + ".jsonl")).open(encoding="utf-8") as stream:
            data[name] = [decode_json(line) for line in stream]
    data["assignments"] = decode_json((directory / "assignments.json").read_text(encoding="utf-8"))
    validate_quality_data(data)
    return data, digest(manifest_bytes)


# RU: Неопределённые результаты не считаем отрицательными предсказаниями.
# EN: Do not count indeterminate results as negative predictions.
def metrics(rows, threshold):
    result = dict(tp=0, fp=0, tn=0, fn=0, indeterminate=0,
                  indeterminate_positive=0, indeterminate_negative=0)
    for row in rows:
        truth, score = row["derivation_relation"], row["score"]
        if score is None:
            result["indeterminate"] += 1
            result["indeterminate_positive" if truth else "indeterminate_negative"] += 1
        else:
            predicted = score >= threshold
            result["tp" if truth and predicted else "fn" if truth else "fp" if predicted else "tn"] += 1
    tp, fp, fn = result["tp"], result["fp"], result["fn"]
    # RU: Нулевой знаменатель означает, что метрика не определена.
    # EN: A zero denominator means the metric is undefined.
    result["precision"] = tp / (tp + fp) if tp + fp else None
    result["recall"] = tp / (tp + fn) if tp + fn else None
    result["f1"] = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
    result["total"] = len(rows)
    result["defined"] = len(rows) - result["indeterminate"]
    result["indeterminate_fraction"] = result["indeterminate"] / len(rows) if rows else None
    result["scope"] = "precision/recall/F1 conditional on defined scores; abstentions reported separately"
    return result


def choose_threshold(rows):
    if not rows or any(row["split"] != "tuning" for row in rows):
        raise ValueError("Threshold selection accepts tuning rows only")
    # RU: Фиксированная сетка включает вариант без положительных предсказаний.
    # EN: The fixed grid includes a policy that never predicts positive.
    candidates = [i / 100 for i in range(101)] + [1.01]
    ranked = []
    for threshold in candidates:
        summary = metrics(rows, threshold)
        ranked.append(((summary["f1"] or 0, summary["precision"] or 0, threshold), summary))
    key, summary = max(ranked, key=lambda item: item[0])
    return dict(threshold=key[2], metrics=summary)


# RU: Готовим только работы выбранной части; оценочные баллы не нужны при настройке.
# EN: Prepare only the selected split; evaluation scores are not used during tuning.
def score_split(data, split, cached=False):
    from school_lab.feature_cache import FeatureCache
    assignments = parse_assignments(data["assignments"])
    needed = {p[key] for p in data["pairs"] if p["split"] == split for key in ("first_id", "second_id")}
    submissions = {raw["submission_id"]: parse_submission(raw) for raw in data["submissions"]
                   if raw["submission_id"] in needed}
    output = []
    for method in METHODS:
        prepared, errors = {}, {}
        cache = FeatureCache(method) if cached else None
        for identifier, submission in submissions.items():
            template = assignments[submission.assignment_id].allowed_template
            try:
                features = (cache.prepare(submission.code, template) if cache else
                            (prepare_token_code if method == "token" else prepare_ast_code)(submission.code, template))
                prepared[identifier] = (PreparedSubmission if method == "token" else PreparedAstSubmission)(submission, features)
            except SubmissionError as error:
                errors[identifier] = dict(code=error.code, field=error.field, message=error.message)
        for pair in data["pairs"]:
            if pair["split"] != split:
                continue
            first, second = pair["first_id"], pair["second_id"]
            row = dict(pair, method=method, score=None, evidence=None,
                       submission_hashes=[submission_hash(submissions[first]), submission_hash(submissions[second])])
            failures = {identifier: errors[identifier] for identifier in (first, second) if identifier in errors}
            if failures:
                row.update(status="error", errors=failures)
            else:
                comparison = (compare_prepared_submissions if method == "token" else compare_ast_submissions)(prepared[first], prepared[second])
                row.update(score=comparison.score, evidence=asdict(comparison),
                           status="defined" if comparison.score is not None else "insufficient_data")
            output.append(row)
    return output


def environment():
    return dict(python=sys.version, platform=platform.platform(), implementation=platform.python_implementation())


def source_hashes():
    root = Path(__file__).parent
    names = ("quality_experiment.py", "ast_features.py", "ast_scopes.py", "ast_comparison.py",
             "prepared_code.py", "token_features.py", "token_evidence.py", "similarity.py",
             "corpus_comparison.py", "feature_cache.py")
    # RU: Нормализуем только окончания строк исходников для Windows/Linux.
    # EN: Normalize source line endings only for Windows/Linux portability.
    return {name: digest((root / name).read_bytes().replace(b"\r\n", b"\n")) for name in names}


def tune(data, corpus_hash):
    rows = score_split(data, "tuning")
    return dict(version=VERSION, corpus_manifest_sha256=corpus_hash, source_sha256=source_hashes(),
                python_minor=list(sys.version_info[:2]), ast_version=AST_VERSION,
                policy=POLICY, grid="0.00 through 1.00 by 0.01, plus 1.01 (reject all)",
                methods={method: choose_threshold([row for row in rows if row["method"] == method]) for method in METHODS},
                environment=environment(), tuning_rows=rows)


def evaluate(data, corpus_hash, frozen):
    if (frozen["version"] != VERSION or frozen["corpus_manifest_sha256"] != corpus_hash
            or frozen["source_sha256"] != source_hashes()
            or frozen["python_minor"] != list(sys.version_info[:2]) or frozen["policy"] != POLICY):
        raise ValueError("Frozen policy does not match corpus, source, runtime, or protocol")
    # RU: Проверяем пороги по настройке, не подбирая их на оценочных метках.
    # EN: Verify thresholds against tuning only, never against evaluation labels.
    verified = tune(data, corpus_hash)
    if frozen["methods"] != verified["methods"] or json_bytes(frozen["tuning_rows"]) != json_bytes(verified["tuning_rows"]):
        raise ValueError("Frozen tuning policy has been changed")
    rows = score_split(data, "evaluation")
    optimized = score_split(data, "evaluation", cached=True)
    if rows != optimized:
        raise AssertionError("Optimization changed scores or evidence")
    for row in rows:
        threshold = frozen["methods"][row["method"]]["threshold"]
        prediction = row["score"] >= threshold if row["score"] is not None else None
        row["review_required"] = prediction
        row["outcome"] = ("indeterminate" if prediction is None else
                          "tp" if prediction and row["derivation_relation"] else
                          "fp" if prediction else "fn" if row["derivation_relation"] else "tn")
    return dict(version=VERSION, corpus_manifest_sha256=corpus_hash,
                frozen_policy_sha256=digest(json_bytes(frozen)), environment=environment(),
                optimization_equivalence=True,
                methods={method: dict(threshold=frozen["methods"][method]["threshold"],
                    **metrics([r for r in rows if r["method"] == method], frozen["methods"][method]["threshold"])) for method in METHODS},
                rows=rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="RU: Оценка качества / EN: Quality evaluation")
    parser.add_argument("phase", choices=("tune", "evaluate"))
    parser.add_argument("--corpus", type=Path, default=Path("data/lab2_quality_v1"))
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    data, corpus_hash = load_corpus(args.corpus)
    if args.phase == "tune":
        result, destination = tune(data, corpus_hash), args.policy
    else:
        if args.output is None:
            parser.error("evaluate requires --output")
        result = evaluate(data, corpus_hash, decode_json(args.policy.read_text(encoding="utf-8")))
        destination = args.output
    destination.parent.mkdir(parents=True, exist_ok=True)
    # RU: Не перезаписываем предыдущий эксперимент.
    # EN: Do not overwrite an existing experiment.
    with destination.open("xb") as stream:
        stream.write(json_bytes(result))
    print(json.dumps(result["methods"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
