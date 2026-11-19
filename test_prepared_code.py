import unittest

from school_lab.prepared_code import prepare_token_code
from school_lab.similarity import jaccard_similarity


class PreparedCodeTests(unittest.TestCase):
    def test_preparation_keeps_features_and_original_positions(self) -> None:
        # RU: Исключаем шаблон, сохраняя позицию самостоятельного кода.
        # EN: Exclude the template while preserving other code positions.
        template = "import math\n"
        prepared = prepare_token_code(
            "import math\n\nvalue = 2\n",
            template,
        )

        self.assertEqual(prepared.allowed_template, template)
        self.assertEqual(prepared.template_lines, (1,))
        self.assertEqual(len(prepared.keys), 1)
        self.assertEqual(len(prepared.occurrences), 1)
        self.assertEqual(prepared.occurrences[0].start_line, 3)
        self.assertEqual(prepared.occurrences[0].end_line, 3)

    def test_template_change_requires_different_preparation(self) -> None:
        # RU: Один код обрабатывается с двумя конфигурациями.
        # EN: Process the same code with two configurations.
        code = "value = 2\n"

        without_template = prepare_token_code(code)
        with_template = prepare_token_code(code, code)

        self.assertEqual(len(without_template.keys), 1)
        self.assertEqual(with_template.keys, frozenset())
        self.assertEqual(with_template.template_lines, (1,))

    def test_prepared_features_can_be_used_for_multiple_comparisons(self) -> None:
        # RU: Подготавливаем каждый текст один раз.
        # EN: Prepare each source text once.
        first = prepare_token_code("value = 2\n")
        second = prepare_token_code("value=2\n")
        third = prepare_token_code("value = 3\n")

        # RU: Повторно используем признаки первой работы.
        # EN: Reuse the first submission's features.
        self.assertEqual(
            jaccard_similarity(first.keys, second.keys),
            1.0,
        )
        self.assertEqual(
            jaccard_similarity(first.keys, third.keys),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()