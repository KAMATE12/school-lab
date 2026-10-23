# RU: Описываем итераторы и менеджеры контекста.
# EN: Describe iterators and context managers.
from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import Protocol


# RU: Описываем общий интерфейс источника строк.
# EN: Describe the shared line-source interface.
class LineSource(Protocol):
    def open(self) -> AbstractContextManager[Iterator[str]]:
        ...


# RU: Предоставляем строки, уже находящиеся в памяти.
# EN: Provide lines already held in memory.
class InMemoryLineSource:
    def __init__(self, lines: Iterable[str]) -> None:
        # RU: Сохраняем строки для повторного открытия источника.
        # EN: Store the lines so the source can be opened again.
        self._lines = tuple(lines)

    @contextmanager
    def open(self) -> Iterator[Iterator[str]]:
        # RU: При каждом открытии создаём новый итератор.
        # EN: Create a new iterator for each opening.
        yield iter(self._lines)


# RU: Читаем строки JSONL из файла UTF-8.
# EN: Read JSONL lines from a UTF-8 file.
class JsonlFileSource:
    def __init__(self, path: Path) -> None:
        self._path = path

    @contextmanager
    def open(self) -> Iterator[Iterator[str]]:
        # RU: Закрываем файл при любом выходе из блока with.
        # EN: Close the file whenever the with block is exited.
        with self._path.open("r", encoding="utf-8") as stream:
            yield stream
