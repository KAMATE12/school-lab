import unittest

from school_lab.token_evidence import (
    build_trigram_occurrences,
    find_template_lines,
)
from school_lab.token_features import (
    build_token_trigrams,
    extract_code_tokens,
)


class TokenEvidenceTests(unittest.TestCase):
    def test_exact_template_matches_and_empty_template(self) -> None:
        # RU: Находим все точные вхождения многострочного шаблона.
        # EN: Find every exact occurrence of a multiline template.
        code = "import math\nimport sys\n\nimport math\nimport sys\n"
        template = "import math\nimport sys\n"

        self.assertEqual(
            find_template_lines(code, template),
            frozenset({1, 2, 4, 5}),
        )
        self.assertEqual(
            find_template_lines(code, ""),
            frozenset(),
        )

        # RU: Изменённые отступы не считаются точным совпадением.
        # EN: Changed indentation is not an exact match.
        self.assertEqual(
            find_template_lines(
                "if True:\n    import math\n",
                "import math\n",
            ),
            frozenset(),
        )

    def test_template_exclusion_does_not_join_separate_parts(self) -> None:
        # RU: Шаблон находится между двумя инструкциями.
        # EN: The template lies between two statements.
        code = "a = 1\nimport math\nb = 2\n"
        tokens = extract_code_tokens(code)
        excluded = find_template_lines(code, "import math\n")

        occurrences = build_trigram_occurrences(tokens, excluded)

        self.assertEqual(
            [(item.start_line, item.end_line) for item in occurrences],
            [(1, 1), (3, 3)],
        )
        self.assertEqual(
            [
                tuple(token_key[1] for token_key in item.key)
                for item in occurrences
            ],
            [
                ("a", "=", "1"),
                ("b", "=", "2"),
            ],
        )

    def test_without_exclusion_matches_existing_features(self) -> None:
        # RU: Новый формат сохраняет прежний смысл признаков.
        # EN: The new representation preserves existing feature semantics.
        tokens = extract_code_tokens("# Heading\n\nx = 1\nx = 1\n")
        occurrences = build_trigram_occurrences(tokens)

        self.assertEqual(
            frozenset(item.key for item in occurrences),
            build_token_trigrams(tokens),
        )
        self.assertEqual(
            (occurrences[0].start_line, occurrences[0].end_line),
            (3, 3),
        )


if __name__ == "__main__":
    unittest.main()