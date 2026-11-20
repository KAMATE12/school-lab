## Lab 2 — verified Windows results

Final Windows run: Python 3.14.7, 114 tests passed, 48 performance measurements completed.
Both methods were evaluated on the same fixed pairs; indeterminate results are reported separately.

- [Russian report — Windows](results/lab2_windows_20261120-053448/REPORT_LAB2_RU.md)
- [Quality results](results/lab2_windows_20261120-053448/evaluation.json)
- [Performance measurements](results/lab2_windows_20261120-053448/performance/performance.json)

The Windows reproduction requested in the earlier instructions is now complete.
The Linux results remain a separate reference experiment.

---

# Python Core — лабораторные работы 1 и 2

Автор: Камате Эммануэль. Группа: M80-103CB-26.

## Лабораторная 2: этап Б — качество и измерения

Корпус зафиксирован коммитом `dee17ba`: 44 работы, 60 пар, 20 непересекающихся семейств.
Добавлены отдельные команды настройки и оценки token/AST, обработка неопределённости,
профилирование, ограниченный кеш точных исходников и сравнение производительности до/после.
Основная траектория — Python Core. Высокий score не доказывает нарушение.

- [Инструкция запуска этапа Б (FR)](STAGE_B_RUN_FR.md)
- [Отчёт измеренного запуска Linux (RU)](results/lab2_reference_linux/REPORT_LAB2_RU.md)
- [Корпус и происхождение (FR)](CORPUS_QUALITY_FR.md)
- [AST и ограничения (FR)](AST_METHOD_FR.md)
- [Top-k (FR)](RANKING_FR.md)
- [Исторический этап А](LAB2_STAGE_A.md)
- [Использование ИИ](AI_USAGE.md)

Windows, из корня проекта:

```powershell
# RU: Запускаем проверку, настройку, оценку и измерения.
# EN: Run validation, tuning, evaluation, and measurements.
powershell -ExecutionPolicy Bypass -File .\run_lab2_stage_b.ps1
```

Результаты каждого Windows-запуска помещаются в `results/lab2_windows_<timestamp>/`.
Локальный отчёт создаётся из этих результатов. Референсный отчёт Linux не является
подтверждением измерений на Windows. Политика порогов привязана к хешам исходников,
корпуса и версии Python; нельзя использовать политику другой среды без повторной настройки.
Конечный тег `lab-2` создаётся после локальных проверок и проверки состава коммита.

Метрики условны на определённых результатах: доля null показана отдельно.
Нагрузочный сценарий — индекс и пять полных запросов (5(N−1) сравнений), а не полный
перебор всех пар. Синтетические измерения нельзя обобщать на реальные работы.

REPORT_RU.pdf, REPORT_RU.md, VERIFICATION.txt и MEASUREMENTS.json — артефакты ЛР 1.
Ниже сохранена её историческая документация; не повторяйте создание тега lab-1.

---

# Лабораторная работа 1: приём работ и расширяемые анализаторы

Автор: Эммануэль Камате. Группа: M80-103CB-26.
Траектория: Python Core. Основной уровень. Python >= 3.12.
Код содержит комментарии на русском и английском. Во время работы программы нет HTTP-запросов; полученный код студентов не исполняется.

## Установка и проверка (Windows PowerShell)
Из корня распакованного проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m unittest discover -v
```

Используется обычная установка. После изменения исходников повторите `pip install .` или используйте `pip install -e .` для разработки. При первой сборке pip может скачать setuptools. Зависимостей времени выполнения вне стандартной библиотеки нет.

## Импорт

```powershell
.\.venv\Scripts\school-lab.exe submissions.jsonl
$LASTEXITCODE
.\.venv\Scripts\school-lab.exe submissions_demo.jsonl
$LASTEXITCODE
.\.venv\Scripts\school-lab.exe invalid_submissions.jsonl
$LASTEXITCODE
```

Ожидаемые результаты: `submissions.jsonl` — 12 accepted, 0 duplicate, 0 errors, код 0; `submissions_demo.jsonl` — 2 accepted, 1 duplicate, 2 errors, код 1; `invalid_submissions.jsonl` — 0 accepted, 0 duplicate, 4 errors, код 1.
Итоговый JSON поступает в stdout; сообщения с номерами строк поступают в stderr. Код 2 означает ошибку аргументов или файла. Ошибка отдельной строки не останавливает импорт.

## Анализ

```powershell
.\.venv\Scripts\python.exe -m school_lab.analyze_cli submissions.jsonl --assignment-id assignment-01 --assignments assignments.json --analyzer length --analyzer template --analyzer ai_declaration --output reports_local.jsonl
$LASTEXITCODE
```

Ожидается 12 принятых работ, 36 отчётов и код 0. Выходной файл должен быть новым: существующий файл не перезаписывается. Для повторного запуска выберите другое имя. Альтернативная установленная команда: `.\.venv\Scripts\school-lab-analyze.exe` с теми же аргументами.

```powershell
Get-Content .\reports_local.jsonl -Encoding UTF8 |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Select-Object submission_id, analyzer_id, review_required
```

Каталог assignments.json — массив объектов с точными полями assignment_id, allowed_template, requirements (массив непустых строк). Идентификаторы уникальны. Вместо каталога можно указать `--template-file template.txt`; одновременно эти параметры использовать нельзя. Без каталога требования пусты. Анализатор template требует каталог или файл шаблона.

## Данные

- submissions.jsonl: 12 публичных синтетических записей, извлечённых из ячейки PUBLIC_SUBMISSIONS преподавательского файла «Лекция.ipynb», без исполнения notebook.
- invalid_submissions.jsonl: четыре специально подготовленные ошибочные записи (пустой student_id, дата без зоны, неизвестное поле, повреждённый JSON).
- submissions_demo.jsonl: ранее разработанный смешанный пример с дубликатом и конфликтом.
- assignments.json и template.txt: явно подготовленная конфигурация демонстрации; шаблон — строка `from typing import Iterable`. Это не утверждение о наличии отдельного исходного assignments.json у преподавателя.
- examples/reports_public.jsonl: результаты проверочного запуска окончательной версии.

Строки кода, включая синтаксически ошибочный Python, хранятся как данные. Они не выполняются. Декларации в синтетическом корпусе не являются декларацией автора проекта; использование ИИ автором описано в AI_USAGE.md.

## Архитектура

models — frozen dataclass; errors — структурированная ошибка; validation — JSON и схема; serialization — канонический JSON и SHA-256; repository — хранение; service — приём; sources — источники строк; importing — последовательный импорт; analyzers — Protocol и три реализации; analysis_service — реестр, запуск и защита входа; report_validation — проверка результата; assignments — каталог заданий; cli/analyze_cli — ввод-вывод.

Источники имеют общий интерфейс open() и используются через with. Контрактные тесты проверяют обе реализации. Анализаторы имеют общий метод analyze(submission, context). Реестр хранит фабрики; центральный сервис не ветвится по классам.

## Семантика

Хеш вычисляется по всем полям Submission: asdict → JSON с sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False → UTF-8 → SHA-256. Пробелы внутри text/code и строка времени сохраняются. Одинаковый ID и хеш дают duplicate; другой хеш при том же ID даёт conflict без замены.

Length считает все непустые строки, включая комментарии; score=null. Template ищет полный точный непрерывный блок строк, без нормализации отступов, и объясняет разрешённое совпадение. Evidence использует исходные номера строк с 1, обе границы включены. AI-анализатор описывает декларацию, проверяет непустые tool/purpose при used=true и запрашивает просмотр при verified_by_student=false. Это не детектор происхождения текста.

## Ограничения

Хранилище живёт только в процессе и не обеспечивает конкурентную атомарность. Frozen и deepcopy не являются песочницей. Сохраняющиеся изменения входа анализатором выявляются сравнением копий. Нет проверки семантической корректности решения и автоматического вердикта о плагиате. Конфигурация и модель протокола ориентированы на учебный синхронный сценарий. Источник памяти хранит строки, файл выдаёт их постепенно. Контекст хранит снимок дополнительных работ; CLI сейчас заполняет только задание, поскольку эти анализаторы не сравнивают студентов. Ошибка анализатора записывается в stderr, отчёт об успешном анализе для него не создаётся; остальные анализаторы продолжают работу. При ошибке ввода-вывода выходной файл может быть частичным.

## Сдача и Git

Перед сдачей перечитайте AI_USAGE.md и REPORT_RU.pdf, проверьте имя и группу. Не включайте .venv, кэши, пароли и реальные работы студентов.
При наличии репозитория выполните git status, добавьте проверенные исходники, тесты, данные и документацию, создайте итоговый коммит, затем:

```powershell
git tag -a lab-1 -m "Laboratory 1: acceptance and extensible analyzers"
git show --stat lab-1
```

Если тег существует, сначала проверьте его; не заменяйте его автоматически. Промежуточный lab-1-stage-a следует ставить только на реальный промежуточный коммит, а не выдавать финальный коммит за исторический этап A. Эта поставка не создаёт коммиты и теги в репозитории студента. Отправка тега на сервер выполняется студентом при необходимости.

## Проверенные результаты

Подробности среды и команды: VERIFICATION.txt. Общий набор тестов, ошибки входа, контракты, границы evidence, сохранение данных, закрытие ресурсов и CLI проверяются автоматически. Число тестов не заменяет проверку требований.

Повторить измерение: `.\\.venv\\Scripts\\python.exe benchmark.py`. Время зависит от машины; фиксированные пороги не заданы.
