import ast
import io
import tokenize
from dataclasses import dataclass

from school_lab.errors import SubmissionError


# RU: Сохраняем тип, текст и исходные позиции токена.
# EN: Store the token type, text, and original positions.
@dataclass(frozen=True)
class CodeToken:
    kind: str
    text: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int


# RU: Определяем категории, исключаемые из сравнения.
# EN: Define categories excluded from comparison.
IGNORED_TOKEN_TYPES = frozenset({
    tokenize.COMMENT,
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENDMARKER,
    tokenize.ENCODING,
})


# RU: Извлекаем токены без выполнения исходного кода.
# EN: Extract tokens without executing the source code.
def extract_code_tokens(code: str) -> tuple[CodeToken, ...]:
    try:
        # RU: Проверяем синтаксис до разбиения на токены.
        # EN: Check syntax before tokenization.
        ast.parse(code)

        tokens: list[CodeToken] = []

        with io.StringIO(code) as stream:
            for item in tokenize.generate_tokens(stream.readline):
                # RU: Пропускаем комментарии и служебные токены.
                # EN: Skip comments and structural tokens.
                if item.type in IGNORED_TOKEN_TYPES:
                    continue

                # RU: Сохраняем позиции из исходного текста.
                # EN: Preserve positions from the original text.
                tokens.append(
                    CodeToken(
                        kind=tokenize.tok_name[item.type],
                        text=item.string,
                        start_line=item.start[0],
                        start_column=item.start[1],
                        end_line=item.end[0],
                        end_column=item.end[1],
                    )
                )

    except (SyntaxError, tokenize.TokenError) as error:
        # RU: Возвращаем понятную структурированную ошибку.
        # EN: Raise an understandable structured error.
        raise SubmissionError(
            code="invalid_code",
            field="code",
            message=(
                "Некорректный синтаксис Python / "
                f"Invalid Python syntax: {error}"
            ),
        ) from error

    # RU: Возвращаем неизменяемую последовательность токенов.
    # EN: Return an immutable sequence of tokens.
    return tuple(tokens)

# RU: Описываем содержимое одного токена.
# EN: Describe the content of one token.
type TokenKey = tuple[str, str]

# RU: Описываем группу из трёх токенов.
# EN: Describe a group of three tokens.
type TrigramKey = tuple[TokenKey, TokenKey, TokenKey]


# RU: Строим множество уникальных триграмм.
# EN: Build a set of unique trigrams.
def build_token_trigrams(
    tokens: tuple[CodeToken, ...],
) -> frozenset[TrigramKey]:
    # RU: Сохраняем категорию и текст каждого токена.
    # EN: Keep each token's category and text.
    keys: list[TokenKey] = [
        (item.kind, item.text)
        for item in tokens
    ]

    trigrams: set[TrigramKey] = set()

    # RU: Перемещаем окно из трёх элементов.
    # EN: Move a window of three elements.
    for index in range(len(keys) - 2):
        trigram = (
            keys[index],
            keys[index + 1],
            keys[index + 2],
        )
        trigrams.add(trigram)

    return frozenset(trigrams)