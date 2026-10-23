# RU: Используем JSON, SHA-256 и преобразование dataclass.
# EN: Use JSON, SHA-256, and dataclass conversion.
import hashlib
import json
from dataclasses import asdict

# RU: Используем общую модель отправленной работы.
# EN: Use the shared submission model.
from school_lab.models import Submission


# RU: Преобразуем работу, включая вложенные dataclass, в словарь.
# EN: Convert the submission, including nested dataclasses, to a dictionary.
def submission_to_dict(submission: Submission) -> dict:
    return asdict(submission)


# RU: Создаём JSON с фиксированными правилами форматирования.
# EN: Create JSON using fixed formatting rules.
def canonical_json(data: dict) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


# RU: Вычисляем SHA-256 для всех полей работы.
# EN: Compute SHA-256 over all submission fields.
def submission_hash(submission: Submission) -> str:
    # RU: Получаем словарь с данными работы.
    # EN: Obtain a dictionary containing the submission data.
    data = submission_to_dict(submission)

    # RU: Создаём стабильное текстовое представление.
    # EN: Create a stable text representation.
    canonical_text = canonical_json(data)

    # RU: Преобразуем текст в байты UTF-8.
    # EN: Convert the text to UTF-8 bytes.
    canonical_bytes = canonical_text.encode("utf-8")

    # RU: Возвращаем хеш в виде шестнадцатеричной строки.
    # EN: Return the hash as a hexadecimal string.
    return hashlib.sha256(canonical_bytes).hexdigest()
