from dataclasses import dataclass, field


# RU: Храним соответствия имён для одной области видимости.
# EN: Store name mappings for one scope.
@dataclass
class NameScope:
    # RU: Каждая область получает собственный словарь.
    # EN: Each scope receives its own dictionary.
    replacements: dict[str, str] = field(default_factory=dict)

    # RU: Возвращаем постоянную замену для указанного имени.
    # EN: Return a consistent replacement for the given name.
    def normalize(self, original_name: str) -> str:
        # RU: Новое имя получает следующий свободный номер.
        # EN: A new name receives the next available number.
        if original_name not in self.replacements:
            number = len(self.replacements)
            self.replacements[original_name] = f"name_{number}"

        # RU: Уже известное имя сохраняет прежнюю замену.
        # EN: An already known name keeps its existing replacement.
        return self.replacements[original_name]