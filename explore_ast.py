import ast


def main() -> None:
    # RU: Анализируем текст, не выполняя умножение.
    # EN: Analyze text without executing the multiplication.
    code = "total = price * quantity\n"
    tree = ast.parse(code)

    # RU: Показываем структуру дерева без исходных позиций.
    # EN: Display the tree structure without source positions.
    print("AST:")
    print(ast.dump(tree, indent=4, include_attributes=False))

    # RU: Получаем первую инструкцию программы.
    # EN: Retrieve the first statement of the program.
    statement = tree.body[0]

    print("Statement type:", type(statement).__name__)
    print("Target:", statement.targets[0].id)
    print("Operation:", type(statement.value.op).__name__)
    print("Left operand:", statement.value.left.id)
    print("Right operand:", statement.value.right.id)

    # RU: Сравниваем структуры с разным оформлением и именами.
    # EN: Compare structures with different formatting and names.
    formatted_tree = ast.parse(
        "total=price*quantity  # Same calculation\n"
    )
    renamed_tree = ast.parse("result = cost * count\n")

    original = ast.dump(tree, include_attributes=False)
    formatted = ast.dump(formatted_tree, include_attributes=False)
    renamed = ast.dump(renamed_tree, include_attributes=False)

    print("Same AST after formatting:", original == formatted)
    print("Same AST after renaming:", original == renamed)


if __name__ == "__main__":
    main()