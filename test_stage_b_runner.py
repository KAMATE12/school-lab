import tempfile
import unittest
from pathlib import Path

from benchmark_lab2 import make_load, workload


class BenchmarkContractTests(unittest.TestCase):
    def test_seed_reproduces_load_and_cache_preserves_evidence_checksum(self):
        # RU: Проверяем воспроизводимость и равенство результатов обоих путей.
        # EN: Check reproducibility and equal outputs from both execution paths.
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.jsonl", Path(directory) / "b.jsonl"
            make_load(first, 40)
            make_load(second, 40)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            for method in ("token", "ast"):
                before, after = workload(first, method, False), workload(first, method, True)
                self.assertEqual(before["comparisons"], 5 * 39)
                self.assertEqual(before["result_sha256"], after["result_sha256"])
                self.assertGreater(after["cache_hits"], 0)

    def test_unique_control_has_no_cache_hits(self):
        # RU: Контроль уникальных текстов не создаёт искусственных попаданий в кеш.
        # EN: The unique-source control must not create artificial cache hits.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unique.jsonl"
            make_load(path, 10, unique=True)
            self.assertEqual(workload(path, "ast", True)["cache_hits"], 0)


if __name__ == "__main__":
    unittest.main()
