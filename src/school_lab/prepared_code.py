from dataclasses import dataclass

from school_lab.token_evidence import (
    TrigramOccurrence,
    build_trigram_occurrences,
    find_template_lines,
)
from school_lab.token_features import (
    TrigramKey,
    extract_code_tokens,
)


# RU: Храним подготовленные признаки одного исходного текста.
# EN: Store the prepared features of one source text.
@dataclass(frozen=True)
class PreparedTokenCode:
    keys: frozenset[TrigramKey]
    occurrences: tuple[TrigramOccurrence, ...]
    template_lines: tuple[int, ...]
    allowed_template: str


# RU: Подготавливаем признаки для последующего повторного использования.
# EN: Prepare features for subsequent reuse.
def prepare_token_code(
    code: str,
    allowed_template: str = "",
) -> PreparedTokenCode:
    # RU: Находим разрешённый шаблон в исходном тексте.
    # EN: Locate the allowed template in the original text.
    excluded_lines = find_template_lines(code, allowed_template)

    # RU: Извлекаем токены и сохраняем допустимые триграммы.
    # EN: Extract tokens and retain eligible trigrams.
    tokens = extract_code_tokens(code)
    occurrences = build_trigram_occurrences(
        tokens,
        excluded_lines,
    )

    # RU: Отделяем уникальные ключи от отдельных вхождений.
    # EN: Separate unique keys from individual occurrences.
    keys = frozenset(item.key for item in occurrences)

    return PreparedTokenCode(
        keys=keys,
        occurrences=occurrences,
        template_lines=tuple(sorted(excluded_lines)),
        allowed_template=allowed_template,
    )