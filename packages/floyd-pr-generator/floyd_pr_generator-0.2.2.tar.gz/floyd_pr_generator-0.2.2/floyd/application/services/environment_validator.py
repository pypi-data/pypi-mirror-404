
from floyd.adapters.outbound.utils.terminal import Terminal
from floyd.domain.value_objects.ai_provider import ProviderType


class EnvironmentValidator:
    def __init__(self, terminal: Terminal):
        self._terminal = terminal

    def validate_core_dependencies(self) -> None:
        self._terminal.ensure_installed("git")
        self._terminal.ensure_installed("gh")

        if not (self._terminal.is_installed("python") or self._terminal.is_installed("python3")):
            from floyd.domain.exceptions.terminal.missing_dependency_exception import MissingDependencyException
            raise MissingDependencyException("python")

    def validate_ai_provider(self, provider: ProviderType) -> None:
        tool_name = provider.value

        if tool_name:
            self._terminal.ensure_installed(tool_name)

