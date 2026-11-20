"""Sequential load benchmark: feature index plus five exhaustive query scans."""
import argparse
import cProfile
import gc
import hashlib
import io
import json
import platform
import pstats
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

from school_lab.ast_comparison import PreparedAstSubmission, compare_ast_submissions
from school_lab.ast_features import prepare_ast_code
from school_lab.corpus_comparison import compare_prepared_submissions
from school_lab.corpus_pairs import PreparedSubmission
from school_lab.feature_cache import FeatureCache
from school_lab.prepared_code import prepare_token_code
from school_lab.quality_corpus import build_quality_data
from school_lab.quality_experiment import json_bytes, source_hashes
from school_lab.validation import decode_json, parse_submission

SEED = 20261120


# RU: Создаём нагрузочные данные отдельно от размеченного корпуса качества.
# EN: Generate load data separately from the annotated quality corpus.
def make_load(path, size, unique=False):
    source = build_quality_data()["submissions"][0]
    rng = random.Random(SEED)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for index in range(size):
            variant = index if unique else rng.randrange(32)
            raw = dict(source, submission_id=f"load-{index}", student_id=f"student-{index}",
                       assignment_id="load", template_id=None,
                       code=f"def solve(values):\n    return sum(x * x for x in values if x >= {variant})\n")
            stream.write(json.dumps(raw, ensure_ascii=False) + "\n")


# RU: Читаем по строкам, сохраняем индекс признаков, выполняем пять полных запросов.
# EN: Read line by line, retain a feature index, and run five exhaustive queries.
def workload(path, method, optimized):
    cache = FeatureCache(method) if optimized else None
    prepare = prepare_token_code if method == "token" else prepare_ast_code
    wrapper = PreparedSubmission if method == "token" else PreparedAstSubmission
    compare = compare_prepared_submissions if method == "token" else compare_ast_submissions
    index = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            submission = parse_submission(decode_json(line))
            features = cache.prepare(submission.code) if cache else prepare(submission.code)
            index.append(wrapper(submission, features))
    checksum, count = hashlib.sha256(), 0
    for query in index[:5]:
        for candidate in index:
            if query.submission.submission_id == candidate.submission.submission_id:
                continue
            comparison = compare(query, candidate)
            # RU: Хешируем результат без хранения всех сравнений в памяти.
            # EN: Hash the result without retaining all comparisons in memory.
            checksum.update(json.dumps({
                "first": comparison.first_id, "second": comparison.second_id,
                "score": comparison.score,
                "first_matches": [(str(x.key), x.start_line, x.end_line) for x in comparison.first_matches],
                "second_matches": [(str(x.key), x.start_line, x.end_line) for x in comparison.second_matches],
                "templates": [comparison.first_template_lines, comparison.second_template_lines],
            }, sort_keys=True).encode("utf-8"))
            count += 1
    return dict(records=len(index), comparisons=count, result_sha256=checksum.hexdigest(),
                cache_hits=cache.hits if cache else 0, cache_misses=cache.misses if cache else len(index))


def main(argv=None):
    parser = argparse.ArgumentParser(description="RU: Измерения / EN: Sequential measurements")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    if args.repeats < 3:
        parser.error("At least three repetitions are required")
    # RU: Новый каталог предотвращает смешивание разных запусков.
    # EN: A new directory prevents mixing different experiment runs.
    args.output.mkdir(parents=True, exist_ok=False)
    files = {}
    for size in (100, 1000, 5000):
        files[size] = args.output / f"load_{size}.jsonl"
        make_load(files[size], size)
    unique = args.output / "load_unique_1000.jsonl"
    make_load(unique, 1000, unique=True)
    # RU: Сначала профилируем исходный вариант, отдельно от измерений времени.
    # EN: Profile the baseline first, separately from timed measurements.
    for method in ("token", "ast"):
        for optimized in (False, True):
            label = "cached" if optimized else "baseline"
            profile = cProfile.Profile()
            profile.runcall(workload, files[1000], method, optimized)
            profile.dump_stats(str(args.output / f"profile_{method}_{label}.prof"))
            buffer = io.StringIO()
            pstats.Stats(profile, stream=buffer).sort_stats("cumulative").print_stats(30)
            (args.output / f"profile_{method}_{label}.txt").write_text(buffer.getvalue(), encoding="utf-8")
    measurements = []
    for scenario, paths in (("repeated_32_sources", files), ("unique_sources", {1000: unique})):
        for size, path in paths.items():
            for method in ("token", "ast"):
                runs = {False: [], True: []}
                # RU: Чередуем порядок вариантов, чтобы уменьшить влияние прогрева.
                # EN: Alternate variant order to reduce warm-up order bias.
                for repetition in range(args.repeats):
                    for optimized in ((False, True) if repetition % 2 == 0 else (True, False)):
                        gc.collect()
                        tracemalloc.start()
                        start = time.perf_counter()
                        try:
                            result = workload(path, method, optimized)
                            elapsed = time.perf_counter() - start
                            _, peak = tracemalloc.get_traced_memory()
                        finally:
                            tracemalloc.stop()
                        runs[optimized].append(dict(repetition=repetition + 1, wall_seconds=elapsed,
                                                    peak_python_bytes=peak, **result))
                        print(f"{scenario} n={size} {method} cached={optimized} run={repetition+1} seconds={elapsed:.3f}", flush=True)
                checksums = {r["result_sha256"] for items in runs.values() for r in items}
                if len(checksums) != 1:
                    raise AssertionError("Optimization changed comparisons")
                for optimized, items in runs.items():
                    measurements.append(dict(scenario=scenario, records=size, method=method,
                        optimized=optimized, runs=items,
                        median_wall_seconds=statistics.median(r["wall_seconds"] for r in items),
                        median_peak_python_bytes=statistics.median(r["peak_python_bytes"] for r in items)))
                # RU: Сохраняем промежуточные результаты после каждого размера и метода.
                # EN: Save a checkpoint after each size and method.
                (args.output / "checkpoint.json").write_bytes(json_bytes(measurements))
    report = dict(seed=SEED, repeats=args.repeats, environment=dict(python=sys.version, platform=platform.platform()),
                  source_sha256=source_hashes(), measurements=measurements,
                  workload="JSONL validation + retained index + 5 exhaustive query scans; 5*(N-1) directed comparisons",
                  limitations=["Not a full N*(N-1)/2 all-pairs benchmark", "Peak is tracemalloc-traced Python allocations, not process RSS",
                               "Timing includes tracemalloc overhead; sequential single process", "Synthetic load is not quality evaluation",
                               "Cache is bounded to 128 exact (code, template) entries; repeated-source benefit is workload-dependent"],
                  inputs_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (*files.values(), unique)})
    (args.output / "performance.json").write_bytes(json_bytes(report))
    print("Saved:", args.output / "performance.json")


if __name__ == "__main__":
    main()
