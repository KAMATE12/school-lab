"""Display how a new teacher template changes feature configuration."""
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from school_lab.ast_features import prepare_ast_code
from school_lab.prepared_code import prepare_token_code
from school_lab.quality_experiment import source_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-file", type=Path, required=True)
    parser.add_argument("--template-file", type=Path, required=True)
    args = parser.parse_args()
    # RU: Читаем новые исходники и шаблон, не изменяя зафиксированный корпус.
    # EN: Read new source and template files without changing the fixed corpus.
    code = args.code_file.read_text(encoding="utf-8")
    template = args.template_file.read_text(encoding="utf-8")
    output = dict(source_sha256=source_hashes(), code_sha256=hashlib.sha256(code.encode()).hexdigest(), variants=[])
    for label, allowed in (("without_template", ""), ("with_new_template", template)):
        token, ast = prepare_token_code(code, allowed), prepare_ast_code(code, allowed)
        output["variants"].append(dict(
            label=label, template_sha256=hashlib.sha256(allowed.encode()).hexdigest(),
            ast_config_hash=ast.config_hash, token_features=len(token.keys), ast_features=len(ast.keys),
            token_template_lines=token.template_lines, ast_template_lines=ast.template_lines,
            ast_occurrences=[dict(start_line=x.start_line, end_line=x.end_line) for x in ast.occurrences],
        ))
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
