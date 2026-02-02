class BaseError(Exception):
    """
    Base exception for all ms api errors.
    """


class DetailedMoyskladAPIError(BaseError):
    """
    Base exception for all ms api errors with detailed message.
    """

    url: str | None = None

    def __init__(self, message: str, code: int | None = None) -> None:
        self.message = message
        self.code = code

    def __str__(self) -> str:
        message = self.message

        if self.code:
            message += (
                f"\n(ссылка на документацию с описанием ошибки {self.code}: {self.url})"
            )
        else:
            if self.url:
                message += f"\n(ссылка на документацию с описанием ошибки: {self.url})"

        return message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"


class TokenValidationError(Exception):
    pass


class MoyskladAPIError(DetailedMoyskladAPIError):
    def __init__(
        self, message: str, code: int | None = None, url: str | None = None
    ) -> None:
        super().__init__(message, code)
        self.url = url
