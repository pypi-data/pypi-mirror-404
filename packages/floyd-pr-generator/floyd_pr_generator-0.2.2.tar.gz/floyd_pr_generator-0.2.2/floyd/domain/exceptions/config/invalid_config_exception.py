from floyd.domain.exceptions.domain_exception import DomainException


class InvalidConfigException(DomainException):
    def __init__(self, message: str) -> None:
        super().__init__(message)
