"""Deterministic synthetic quality corpus. No similarity scores or code execution."""
import ast
import hashlib
import io
import itertools
import json
import tokenize
from collections import Counter
from pathlib import Path

from school_lab.assignments import parse_assignments
from school_lab.validation import parse_submission

CORPUS_VERSION = "lab2-quality-v1"
TEMPLATE = "from typing import Iterable"

# RU: Учебные корни используют публичные примеры и новые синтетические реализации.
# EN: Learning roots use public examples and newly authored synthetic implementations.
ROOTS = {
    "sum_squares": [
        ("generator_sum", "def solve(values: Iterable[int]) -> int:\n    return sum(x * x for x in values if x >= 0)\n",
         {"values":"numbers", "x":"element"}),
        ("loop_accumulator", "def solve(values: Iterable[int]) -> int:\n    total = 0\n    for value in values:\n        if value >= 0:\n            total += value ** 2\n    return total\n",
         {"values":"items", "total":"answer", "value":"entry"}),
        ("filter_map", "def solve(values: Iterable[int]) -> int:\n    positive = filter(lambda x: x >= 0, values)\n    squares = map(lambda y: y * y, positive)\n    return sum(squares)\n",
         {"values":"sequence", "positive":"kept", "squares":"results", "x":"item", "y":"number"}),
        ("recursive_list", "def solve(values: Iterable[int]) -> int:\n    items = list(values)\n    if not items:\n        return 0\n    first = items[0]\n    contribution = first ** 2 if first >= 0 else 0\n    return contribution + solve(items[1:])\n",
         {"values":"data", "items":"entries", "first":"head", "contribution":"part"}),
        ("while_index", "def solve(values: Iterable[int]) -> int:\n    entries = list(values)\n    index = 0\n    answer = 0\n    while index < len(entries):\n        current = entries[index]\n        if current >= 0:\n            answer = answer + current * current\n        index += 1\n    return answer\n",
         {"values":"numbers", "entries":"data", "index":"position", "answer":"total", "current":"element"}),
        ("reduce", "from functools import reduce\n\ndef solve(values: Iterable[int]) -> int:\n    return reduce(lambda acc, item: acc + (item * item if item >= 0 else 0), values, 0)\n",
         {"values":"numbers", "acc":"running", "item":"value"}),
    ],
    "count_even": [
        ("generator_count", "def solve(values: Iterable[int]) -> int:\n    return sum(1 for item in values if item % 2 == 0)\n",
         {"values":"numbers", "item":"element"}),
        ("loop_counter", "def solve(values: Iterable[int]) -> int:\n    count = 0\n    for number in values:\n        if number % 2 == 0:\n            count += 1\n    return count\n",
         {"values":"items", "count":"answer", "number":"entry"}),
        ("filter_length", "def solve(values: Iterable[int]) -> int:\n    selected = filter(lambda value: value % 2 == 0, values)\n    return len(list(selected))\n",
         {"values":"sequence", "selected":"kept", "value":"item"}),
        ("recursive_count", "def solve(values: Iterable[int]) -> int:\n    items = list(values)\n    if len(items) == 0:\n        return 0\n    head_count = 1 if items[0] % 2 == 0 else 0\n    return head_count + solve(items[1:])\n",
         {"values":"data", "items":"entries", "head_count":"increment"}),
        ("while_pop", "def solve(values: Iterable[int]) -> int:\n    remaining = list(values)\n    result = 0\n    while remaining:\n        element = remaining.pop()\n        result += int(element % 2 == 0)\n    return result\n",
         {"values":"numbers", "remaining":"pending", "result":"count", "element":"item"}),
        ("partition_lengths", "def solve(values: Iterable[int]) -> int:\n    items = tuple(values)\n    odd = [value for value in items if value % 2 != 0]\n    return len(items) - len(odd)\n",
         {"values":"data", "items":"entries", "odd":"excluded", "value":"number"}),
    ],
}


# RU: Переименовываем только токены NAME, сохраняя остальной текст.
# EN: Rename NAME tokens only, preserving the rest of the text.
def rename_identifiers(code: str, replacements: dict[str, str]) -> str:
    lines = code.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    edits = []
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type == tokenize.NAME and token.string in replacements:
            start = starts[token.start[0] - 1] + token.start[1]
            end = starts[token.end[0] - 1] + token.end[1]
            edits.append((start, end, replacements[token.string]))
    # RU: Идём с конца, чтобы ранние позиции не сдвигались.
    # EN: Work backwards so earlier source positions do not shift.
    for start, end, replacement in reversed(edits):
        code = code[:start] + replacement + code[end:]
    return code


# RU: Меняем только комментарии, пустые строки и концевые пробелы.
# EN: Change only comments, blank lines, and trailing spaces.
def format_variant(code: str) -> str:
    return "# RU: Учебный вариант. / EN: Learning variant.\n\n" + "\n".join(
        line + "  " if line else line for line in code.splitlines()
    ) + "\n"


def _submission(identifier, assignment, code):
    return {
        "schema_version": 1, "submission_id": identifier,
        "student_id": "synthetic-" + identifier, "assignment_id": assignment,
        # RU: Фиксированное учебное время, не дата реальной сдачи студента.
        # EN: Fixed fixture time, not a real student's submission date.
        "submitted_at": "2026-11-19T00:00:00+00:00",
        "text": "Synthetic quality-evaluation fixture.", "code": code,
        "template_id": "shared-typing-import-v1",
        "ai_declaration": {
            "used": True, "tool": "ChatGPT",
            "purpose": "Create synthetic learning fixtures and deterministic variants",
            "verified_by_student": False,
        },
    }


def _pair(first, second, split, relation, template_only, reason):
    return dict(first_id=first, second_id=second, split=split,
                derivation_relation=relation, template_only=template_only,
                annotation_basis=reason)


# RU: Создаём метки по происхождению, не вызывая анализаторы сходства.
# EN: Create labels from provenance without calling similarity analyzers.
def build_quality_data() -> dict:
    submissions, provenance, pairs = [], [], []
    bases = {}
    for assignment, roots in ROOTS.items():
        for index, (algorithm, body, renaming) in enumerate(roots, start=1):
            family = f"{assignment}-family-{index:02d}"
            split = "tuning" if index <= 3 else "evaluation"
            original = TEMPLATE + "\n\n" + body
            base_id = family + "-base"
            bases.setdefault((assignment, split), []).append(base_id)
            variants = [
                ("base", original, None, {}),
                ("renamed", rename_identifiers(original, renaming), base_id, renaming),
                ("formatted", format_variant(original), base_id, {}),
            ]
            ids = []
            for transformation, code, parent, mapping in variants:
                identifier = family + "-" + transformation
                ids.append(identifier)
                submissions.append(_submission(identifier, assignment, code))
                provenance.append(dict(
                    submission_id=identifier, assignment_id=assignment,
                    family_id=family, split=split, parent_id=parent,
                    transformation=transformation, renaming=mapping,
                    algorithm=algorithm, source=(
                        {1: "public_demo_adaptation:sub-001",
                         2: "public_demo_adaptation:sub-004",
                         3: "public_demo_adaptation:sub-006"}.get(index, "synthetic_root_authored_with_ChatGPT_v1")
                        if assignment == "sum_squares" else "synthetic_root_authored_with_ChatGPT_v1"
                    ),
                    annotation_status="construction_based_not_independently_reviewed",
                ))
            for first, second in itertools.combinations(ids, 2):
                pairs.append(_pair(first, second, split, True, False,
                                   "Both examples descend from the same recorded root."))
    for (assignment, split), ids in bases.items():
        for first, second in itertools.combinations(ids, 2):
            pairs.append(_pair(first, second, split, False, False,
                               "Distinct declared construction roots for the same task; no within-corpus parent relation."))

    # RU: Контрольные работы содержат только разрешённый шаблон и комментарий.
    # EN: Control submissions contain only the allowed template and a comment.
    for split in ("tuning", "evaluation"):
        ids = []
        for index in range(1, 5):
            family = f"scaffold-{split}-{index:02d}"
            identifier = family + "-base"
            ids.append(identifier)
            submissions.append(_submission(identifier, "sum_squares",
                                           TEMPLATE + f"\n# Synthetic scaffold {split} {index}\n"))
            provenance.append(dict(
                submission_id=identifier, assignment_id="sum_squares",
                family_id=family, split=split, parent_id=None,
                transformation="template_only_control", renaming={},
                algorithm="no_solution_only_teacher_scaffold",
                source="independent_use_of_the_shared_teacher_template",
                annotation_status="construction_based_not_independently_reviewed",
            ))
        for first, second in itertools.combinations(ids, 2):
            pairs.append(_pair(first, second, split, False, True,
                               "Only the allowed scaffold is shared; no student solution is present."))
    assignments = [dict(
        assignment_id="sum_squares", allowed_template=TEMPLATE,
        requirements=["Return the sum of squares of the nonnegative input integers."],
    ), dict(
        assignment_id="count_even", allowed_template=TEMPLATE,
        requirements=["Return the number of even integers in the input iterable."],
    )]
    return dict(submissions=submissions, provenance=provenance,
                pairs=pairs, assignments=assignments)


# RU: Проверяем схему, происхождение, разделение семейств и аннотации.
# EN: Validate schema, provenance, family separation, and annotations.
def validate_quality_data(data: dict) -> dict:
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    assignments = parse_assignments(data["assignments"])
    submissions = {}
    for raw in data["submissions"]:
        submission = parse_submission(raw)
        require(submission.submission_id not in submissions, "Duplicate submission ID")
        require(submission.assignment_id in assignments, "Unknown assignment")
        ast.parse(submission.code)  # RU: Не исполняем. / EN: Do not execute.
        submissions[submission.submission_id] = submission
    metadata, family_split, family_assignment = {}, {}, {}
    for item in data["provenance"]:
        identifier, family, split = item["submission_id"], item["family_id"], item["split"]
        require(identifier in submissions and identifier not in metadata, "Invalid provenance ID")
        require(isinstance(family, str) and bool(family), "Invalid family ID")
        require(split in ("tuning", "evaluation"), "Invalid split")
        require(item["assignment_id"] == submissions[identifier].assignment_id, "Provenance assignment mismatch")
        require(family_split.setdefault(family, split) == split, "Family leakage between splits")
        require(family_assignment.setdefault(family, item["assignment_id"]) == item["assignment_id"],
                "Family crosses assignments")
        metadata[identifier] = item
    require(set(metadata) == set(submissions), "Missing provenance")
    roots_per_family = Counter(
        item["family_id"] for item in metadata.values() if item["parent_id"] is None
    )
    require(all(roots_per_family[family] == 1 for family in family_split), "Each family needs one root")
    for identifier, item in metadata.items():
        parent = item["parent_id"]
        code = submissions[identifier].code
        if item["transformation"] in ("renamed", "formatted"):
            require(parent in metadata and parent != identifier, "Missing or invalid parent")
            ancestor = metadata[parent]
            require(ancestor["transformation"] == "base", "Parent must be an original root")
            require(ancestor["family_id"] == item["family_id"], "Parent family mismatch")
            require(ancestor["split"] == item["split"], "Parent split mismatch")
            original = submissions[parent].code
            expected = (rename_identifiers(original, item["renaming"])
                        if item["transformation"] == "renamed" else format_variant(original))
            require(code == expected, "Variant does not match its recorded transformation")
        else:
            require(parent is None, "A root must not have a parent")
            require(item["transformation"] in ("base", "template_only_control"), "Unknown transformation")
            if item["transformation"] == "template_only_control":
                template = assignments[item["assignment_id"]].allowed_template
                require(ast.dump(ast.parse(code)) == ast.dump(ast.parse(template)),
                        "Template-only control contains additional code")
    seen_pairs = set()
    counts = {split: Counter() for split in ("tuning", "evaluation")}
    for pair in data["pairs"]:
        first, second = pair["first_id"], pair["second_id"]
        require(first in submissions and second in submissions and first != second, "Invalid pair IDs")
        identity = tuple(sorted((first, second)))
        require(identity not in seen_pairs, "Duplicate unordered pair")
        seen_pairs.add(identity)
        a, b = submissions[first], submissions[second]
        ma, mb = metadata[first], metadata[second]
        require(a.assignment_id == b.assignment_id, "Pair crosses assignments")
        require(a.student_id != b.student_id, "Pair has the same student")
        require(ma["split"] == mb["split"] == pair["split"], "Pair crosses splits")
        require(type(pair["derivation_relation"]) is bool and type(pair["template_only"]) is bool,
                "Labels must be booleans")
        require(pair["derivation_relation"] == (ma["family_id"] == mb["family_id"]),
                "Derivation label conflicts with this corpus's family provenance")
        only_template = all(m["transformation"] == "template_only_control" for m in (ma, mb))
        require(pair["template_only"] == only_template, "Template-only label conflicts with provenance")
        require(isinstance(pair["annotation_basis"], str) and bool(pair["annotation_basis"].strip()),
                "Missing annotation rationale")
        c = counts[pair["split"]]
        c["pairs"] += 1
        c["positive" if pair["derivation_relation"] else "negative"] += 1
        c["template_only"] += pair["template_only"]
    require(len(submissions) >= 30 and len(seen_pairs) >= 40, "Corpus below required size")
    require(sum(c["template_only"] for c in counts.values()) >= 5, "Too few template-only pairs")
    for split, c in counts.items():
        require(c["positive"] > 0 and c["negative"] > 0, "Each split needs both label classes")
    return dict(submissions=len(submissions), families=len(family_split), pairs=len(seen_pairs),
                family_overlap=0, splits={key: dict(value) for key, value in counts.items()})


# RU: Формируем байты файлов детерминированно, без текущего времени и случайности.
# EN: Produce deterministic file bytes without current time or randomness.
def corpus_files(data: dict) -> dict[str, bytes]:
    summary = validate_quality_data(data)
    encode = lambda obj: json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    files = {}
    for name in ("submissions", "provenance", "pairs"):
        text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in data[name])
        files[name + ".jsonl"] = text.encode("utf-8")
    files["assignments.json"] = encode(data["assignments"]).encode("utf-8")
    # RU: Сохраняем окончания строк LF при работе с Git на Windows.
    # EN: Preserve LF line endings when using Git on Windows.
    files[".gitattributes"] = b"*.json text eol=lf\n*.jsonl text eol=lf\n.gitattributes text eol=lf\n"
    manifest = dict(
        corpus_version=CORPUS_VERSION, seed=None,
        split_policy="explicit families 01-03 tuning, 04-06 evaluation; scaffold controls split separately",
        provenance_policy="synthetic construction labels, not an independent human annotation",
        summary=summary,
        sha256={name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
    )
    files["manifest.json"] = encode(manifest).encode("utf-8")
    return files


def write_quality_corpus(destination: Path) -> dict:
    data = build_quality_data()
    files = corpus_files(data)
    if destination.exists():
        # RU: Повторный запуск проверяет файлы, не перезаписывая исправления пользователя.
        # EN: A repeated run checks files without overwriting user edits.
        for name, expected in files.items():
            path = destination / name
            if not path.is_file() or path.read_bytes() != expected:
                raise ValueError(f"Existing corpus differs: {path}; use a new output directory")
    else:
        destination.mkdir(parents=True)
        for name, content in files.items():
            (destination / name).write_bytes(content)
    return validate_quality_data(data)
