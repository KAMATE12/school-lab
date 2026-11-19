import unittest

from school_lab.similarity import jaccard_similarity
from school_lab.token_features import (
    build_token_trigrams,
    extract_code_tokens,
)


class SimilarityTests(unittest.TestCase):
    def test_five_tokens_produce_three_expected_trigrams(self) -> None:
        # RU: Проверяем состав групп и их перекрытие.
        # EN: Check group contents and their overlap.
        tokens = extract_code_tokens("total = price * quantity\n")
        trigrams = build_token_trigrams(tokens)

        texts = {
            tuple(key[1] for key in trigram)
            for trigram in trigrams
        }

        self.assertEqual(
            texts,
            {
                ("total", "=", "price"),
                ("=", "price", "*"),
                ("price", "*", "quantity"),
            },
        )

    def test_formatting_and_comments_give_score_one(self) -> None:
        # RU: Разное оформление сохраняет одинаковые признаки.
        # EN: Different formatting preserves identical features.
        first = build_token_trigrams(
            extract_code_tokens("total = price * quantity\n")
        )
        second = build_token_trigrams(
            extract_code_tokens(
                "total=price*quantity  # Calculate total\n"
            )
        )

        self.assertEqual(jaccard_similarity(first, second), 1.0)

    def test_operator_change_gives_one_fifth(self) -> None:
        # RU: Один общий триграмм из пяти уникальных.
        # EN: One shared trigram out of five unique trigrams.
        first = build_token_trigrams(
            extract_code_tokens("total = price * quantity\n")
        )
        second = build_token_trigrams(
            extract_code_tokens("total = price + quantity\n")
        )

        self.assertAlmostEqual(
            jaccard_similarity(first, second),
            0.2,
        )
        self.assertEqual(
            jaccard_similarity(first, second),
            jaccard_similarity(second, first),
        )

    def test_short_inputs_have_insufficient_data(self) -> None:
        # RU: Менее трёх токенов не образуют триграмм.
        # EN: Fewer than three tokens cannot form a trigram.
        for code in ("", "pass\n", "return value\n"):
            with self.subTest(code=code):
                features = build_token_trigrams(
                    extract_code_tokens(code)
                )
                self.assertEqual(features, frozenset())
                self.assertIsNone(
                    jaccard_similarity(features, features)
                )

    def test_empty_against_nonempty_gives_zero(self) -> None:
        # RU: Проверяем случай непустого объединения без совпадений.
        # EN: Check a nonempty union with no shared features.
        empty = frozenset()
        nonempty = build_token_trigrams(
            extract_code_tokens("value = 2\n")
        )

        self.assertEqual(
            jaccard_similarity(empty, nonempty),
            0.0,
        )

    def test_repeated_trigrams_are_counted_once(self) -> None:
        # RU: Повтор группы не увеличивает размер множества.
        # EN: Repeating a group does not increase the set size.
        first = build_token_trigrams(
            extract_code_tokens("x = 1\nx = 1\n")
        )
        second = build_token_trigrams(
            extract_code_tokens("x = 1\nx = 1\nx = 1\n")
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)


if __name__ == "__main__":
    unittest.main()