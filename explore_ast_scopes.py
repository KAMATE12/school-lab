from school_lab.ast_scopes import NameScope

def main() -> None:
    # RU: Создаём отдельную область для каждой функции.
    # EN: Create a separate scope for each function.
    double_scope = NameScope()
    increment_scope = NameScope()

    # RU: Первый параметр каждой функции получает name_0.
    # EN: The first parameter of each function receives name_0.
    print("Double parameter:", double_scope.normalize("value"))
    print("Increment parameter:", increment_scope.normalize("number"))

    # RU: Повторное использование сохраняет ту же замену.
    # EN: Repeated use preserves the same replacement.
    print("Double use:", double_scope.normalize("value"))
    print("Increment use:", increment_scope.normalize("number"))

    # RU: Добавляем локальное имя только в первую область.
    # EN: Add a local name to the first scope only.
    print("Double local:", double_scope.normalize("result"))

    # RU: Показываем независимое содержимое словарей.
    # EN: Display the independent dictionary contents.
    print("Double mapping:", double_scope.replacements)
    print("Increment mapping:", increment_scope.replacements)

    # RU: Проверяем, являются ли словари одним объектом.
    # EN: Check whether the dictionaries are the same object.
    print(
        "Same dictionary:",
        double_scope.replacements is increment_scope.replacements,
    )


# RU: Запускаем пример только при прямом запуске файла.
# EN: Run the example only when this file is executed directly.
if __name__ == "__main__":
    main()