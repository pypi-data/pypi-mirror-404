from floyd.domain.exceptions.domain_exception import DomainException


class MissingDependencyException(DomainException):
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"The tool '{tool_name}' was not found. Please ensure it is installed.")
        self.tool_name = tool_name
