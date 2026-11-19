import ast

# RU: Нормализуем имена переменных и параметров.
# EN: Normalize variable and parameter names.
def normalize_simple_names(code: str) -> str:
    # RU: Создаём новое дерево без выполнения программы.
    # EN: Create a fresh tree without executing the program.
    tree = ast.parse(code)

    # RU: Собираем имена переменных и параметры функций.
    # EN: Collect variable names and function parameters.
    name_nodes = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Name, ast.arg)):
            name_nodes.append(node)

    # RU: Обрабатываем имена в порядке появления в тексте.
    # EN: Process names in their source appearance order.
    name_nodes.sort(
        key=lambda node: (node.lineno, node.col_offset)
    )

    # RU: Храним общие соответствия для обеих категорий узлов.
    # EN: Store shared replacements for both node categories.
    replacements: dict[str, str] = {}

    for node in name_nodes:
        # RU: Читаем имя из подходящего атрибута.
        # EN: Read the name from the appropriate attribute.
        if isinstance(node, ast.Name):
            original_name = node.id
        else:
            original_name = node.arg

        # RU: Назначаем номер только новому имени.
        # EN: Assign a number only to a new name.
        if original_name not in replacements:
            replacements[original_name] = (
                f"name_{len(replacements)}"
            )

        normalized_name = replacements[original_name]

        # RU: Записываем новое имя в подходящий атрибут.
        # EN: Write the new name to the appropriate attribute.
        if isinstance(node, ast.Name):
            node.id = normalized_name
        else:
            node.arg = normalized_name

    # RU: Сравниваем структуру без исходных координат.
    # EN: Compare the structure without source coordinates.
    return ast.dump(tree, include_attributes=False)


def main() -> None:
    # RU: Подготавливаем четыре небольших примера.
    # EN: Prepare four small examples.
    original = normalize_simple_names(
        "total = price * quantity\n"
    )
    renamed = normalize_simple_names(
        "result = cost * count\n"
    )
    changed_operator = normalize_simple_names(
        "result = cost + count\n"
    )
    repeated_variable = normalize_simple_names(
        "total = price * price\n"
    )

    # RU: Проверяем, какие изменения сохраняют структуру.
    # EN: Check which changes preserve the structure.
    print("Same after renaming:", original == renamed)
    print("Same after operator change:", original == changed_operator)
    print("Same with repeated variable:", original == repeated_variable)

    # RU: Сравниваем функции после переименования параметра.
    # EN: Compare functions after renaming a parameter.
    first_function = (
        "def double(value):\n"
        "    return value * 2\n"
    )

    second_function = (
        "def double(number):\n"
        "    return number * 2\n"
    )

    first_structure = normalize_simple_names(first_function)
    second_structure = normalize_simple_names(second_function)

    print(
        "Same after parameter renaming:",
        first_structure == second_structure,
    )


# RU: Запускаем пример только при прямом запуске файла.
# EN: Run the example only when the file is executed directly.
if __name__ == "__main__":
    main()