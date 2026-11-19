from dataclasses import dataclass

from school_lab.token_features import CodeToken, TrigramKey


# RU: Храним одно вхождение триграммы в исходном коде.
# EN: Store one trigram occurrence in the original code.
@dataclass(frozen=True)
class TrigramOccurrence:
    key: TrigramKey
    start_line: int
    end_line: int


# RU: Находим строки точных вхождений разрешённого шаблона.
# EN: Find the lines of exact allowed-template occurrences.
def find_template_lines(
    code: str,
    template: str,
) -> frozenset[int]:
    # RU: Пустой шаблон ничего не исключает.
    # EN: An empty template excludes nothing.
    if not template.strip():
        return frozenset()

    code_lines = code.splitlines()
    template_lines = template.splitlines()
    width = len(template_lines)

    matched_lines: set[int] = set()

    for start in range(len(code_lines) - width + 1):
        candidate = code_lines[start:start + width]

        if candidate == template_lines:
            # RU: Переводим индексы с нуля в номера строк с единицы.
            # EN: Convert zero-based indexes to one-based line numbers.
            matched_lines.update(
                range(start + 1, start + width + 1)
            )

    return frozenset(matched_lines)


# RU: Сохраняем триграммы, не пересекающие исключённые строки.
# EN: Keep trigrams that do not cross excluded lines.
def build_trigram_occurrences(
    tokens: tuple[CodeToken, ...],
    excluded_lines: frozenset[int] = frozenset(),
) -> tuple[TrigramOccurrence, ...]:
    occurrences: list[TrigramOccurrence] = []

    for index in range(len(tokens) - 2):
        first = tokens[index]
        second = tokens[index + 1]
        third = tokens[index + 2]

        # RU: Проверяем весь диапазон строк данного окна.
        # EN: Check the entire line range of this window.
        covered_lines = range(
            first.start_line,
            third.end_line + 1,
        )

        if any(line in excluded_lines for line in covered_lines):
            continue

        key: TrigramKey = (
            (first.kind, first.text),
            (second.kind, second.text),
            (third.kind, third.text),
        )

        occurrences.append(
            TrigramOccurrence(
                key=key,
                start_line=first.start_line,
                end_line=third.end_line,
            )
        )

    return tuple(occurrences)