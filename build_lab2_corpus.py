import argparse
import json
from pathlib import Path
from school_lab.quality_corpus import write_quality_corpus


def main():
    # RU: Выбираем отдельный каталог, не меняя примеры лабораторной 1.
    # EN: Choose a separate directory without changing laboratory-1 examples.
    parser = argparse.ArgumentParser(description="Учебный корпус / Learning corpus")
    parser.add_argument("--output", type=Path, default=Path("data/lab2_quality_v1"))
    args = parser.parse_args()
    summary = write_quality_corpus(args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("Corpus directory:", args.output.resolve())


if __name__ == "__main__":
    main()
