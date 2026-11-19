import io
import tokenize


def main() -> None:
    # RU: Храним анализируемый код как текст, не выполняя его.
    # EN: Store the analyzed code as text without executing it.
    code = "total = price * quantity  # Calculate total\n"

    # RU: Предоставляем строку через интерфейс текстового файла.
    # EN: Expose the string through a text-file interface.
    with io.StringIO(code) as stream:
        # RU: Передаём метод чтения строки без его вызова.
        # EN: Pass the line-reading method without calling it.
        tokens = tokenize.generate_tokens(stream.readline)

        # RU: Получаем и показываем токены по одному.
        # EN: Retrieve and display tokens one at a time.
        for item in tokens:
            print(
                tokenize.tok_name[item.type],
                repr(item.string),
                item.start,
                item.end,
            )

if __name__ == "__main__":
    main()