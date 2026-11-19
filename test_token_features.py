import unittest

from school_lab.errors import SubmissionError
from school_lab.token_features import extract_code_tokens


class TokenFeaturesTests(unittest.TestCase):
    def test_spacing_and_comments_preserve_token_content(self) -> None:
        # RU: Сравниваем содержимое токенов, а не их позиции.
        # EN: Compare token content rather than positions.
        first = extract_code_tokens("total = price * quantity\n")
        second = extract_code_tokens(
            "total=price*quantity  # Calculate total\n"
        )

        first_content = [(item.kind, item.text) for item in first]
        second_content = [(item.kind, item.text) for item in second]

        self.assertEqual(first_content, second_content)
        self.assertEqual(
            [item.text for item in first],
            ["total", "=", "price", "*", "quantity"],
        )

    def test_original_line_positions_are_preserved(self) -> None:
        # RU: Комментарий и пустая строка не меняют исходный номер.
        # EN: A comment and a blank line preserve original numbering.
        tokens = extract_code_tokens("# Heading\n\nvalue = 2\n")

        self.assertEqual(tokens[0].text, "value")
        self.assertEqual(tokens[0].start_line, 3)
        self.assertEqual(tokens[0].start_column, 0)
        self.assertEqual(tokens[0].end_column, 5)

    def test_empty_input_and_invalid_syntax(self) -> None:
        # RU: Пустой код не содержит значимых токенов.
        # EN: Empty code contains no retained tokens.
        self.assertEqual(extract_code_tokens(""), ())
        self.assertEqual(extract_code_tokens("# Comment\n"), ())

        # RU: Незакрытая скобка вызывает структурированную ошибку.
        # EN: An unclosed parenthesis raises a structured error.
        with self.assertRaises(SubmissionError) as caught:
            extract_code_tokens("print(")

        self.assertEqual(caught.exception.code, "invalid_code")
        self.assertEqual(caught.exception.field, "code")


if __name__ == "__main__":
    unittest.main()