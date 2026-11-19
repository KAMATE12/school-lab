from school_lab.token_features import TrigramKey


# RU: Вычисляем сходство Жаккара для множеств триграмм.
# EN: Calculate Jaccard similarity for trigram sets.
def jaccard_similarity(
    first: frozenset[TrigramKey],
    second: frozenset[TrigramKey],
) -> float | None:
    # RU: Объединяем все уникальные триграммы.
    # EN: Combine all unique trigrams.
    union = first | second

    # RU: Пустое объединение означает недостаток данных.
    # EN: An empty union means insufficient data.
    if not union:
        return None

    # RU: Находим триграммы, присутствующие в обоих множествах.
    # EN: Find trigrams present in both sets.
    intersection = first & second

    return len(intersection) / len(union)