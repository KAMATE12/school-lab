# RU: Описываем структурированную ошибку обработки работы.
# EN: Define a structured submission-processing error.
class SubmissionError(Exception):
    def __init__(
        self,
        code: str,
        field: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message
