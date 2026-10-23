# RU: Измеряем пять повторов анализа учебного корпуса.
# EN: Measure five analysis runs over the learning corpus.
import json
import platform
from pathlib import Path
from statistics import median
from time import perf_counter
from school_lab.validation import decode_json, parse_submission
from school_lab.assignments import parse_assignments
from school_lab.models import AnalysisContext
from school_lab.analysis_service import analyze_submission


def main() -> None:
    root = Path(__file__).resolve().parent
    records = [parse_submission(decode_json(line)) for line in
               (root / "submissions.jsonl").read_text(encoding="utf-8").splitlines()]
    catalog = parse_assignments(decode_json((root / "assignments.json").read_text(encoding="utf-8")))
    context = AnalysisContext(catalog["assignment-01"])
    durations = []
    for _ in range(5):
        start = perf_counter()
        for submission in records:
            for name in ("length", "template", "ai_declaration"):
                analyze_submission(submission, context, name)
        durations.append((perf_counter() - start) * 1000)
    print(json.dumps({"python": platform.python_version(), "platform": platform.system(),
                     "milliseconds": durations, "median_ms": median(durations)}))


if __name__ == "__main__":
    main()
