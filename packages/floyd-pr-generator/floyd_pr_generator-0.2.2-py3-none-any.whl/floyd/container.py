from dataclasses import dataclass

from floyd.adapters.outbound.ai.claude_adapter import ClaudeAdapter
from floyd.adapters.outbound.ai.copilot_adapter import CopilotAdapter
from floyd.adapters.outbound.ai.gemini_adapter import GeminiAdapter
from floyd.adapters.outbound.config.toml_config_adapter import TomlConfigAdapter
from floyd.adapters.outbound.git.git_cli_adapter import GitCLIAdapter
from floyd.adapters.outbound.github.github_cli_adapter import GitHubCLIAdapter
from floyd.application.ports.outbound.ai_service_port import AIServicePort
from floyd.application.ports.outbound.config_port import ConfigPort
from floyd.application.ports.outbound.git_repository_port import GitRepositoryPort
from floyd.application.ports.outbound.pr_repository_port import PRRepositoryPort
from floyd.application.services.environment_validator import EnvironmentValidator
from floyd.application.services.pr_generation_service import PRGenerationService
from floyd.adapters.outbound.utils.terminal import Terminal
from floyd.domain.exceptions.ai.invalid_provider_exception import (
    InvalidProviderException,
)
from floyd.domain.value_objects.ai_provider import ProviderType


@dataclass
class Container:
    ai_service: AIServicePort
    git_repository: GitRepositoryPort
    pr_repository: PRRepositoryPort
    config: ConfigPort
    pr_generation_service: PRGenerationService


def create_container() -> Container:
    terminal = Terminal()
    config = TomlConfigAdapter()
    validator = EnvironmentValidator(terminal)

    validator.validate_core_dependencies()

    settings = config.get_ai_config()

    validator.validate_ai_provider(settings.provider)

    ADAPTER_MAP = {
        ProviderType.CLAUDE: ClaudeAdapter,
        ProviderType.GEMINI: GeminiAdapter,
        ProviderType.COPILOT: CopilotAdapter,
    }

    adapter_class = ADAPTER_MAP.get(settings.provider)

    if not adapter_class:
        raise InvalidProviderException(f"No adapter registered for {settings.provider}")

    ai_service = adapter_class(terminal)
    git_repository = GitCLIAdapter(terminal)
    pr_repository = GitHubCLIAdapter(terminal)

    pr_generation_service = PRGenerationService(
        ai_service=ai_service,
        git_repository=git_repository,
        pr_repository=pr_repository,
        config=config,
    )

    return Container(
        ai_service=ai_service,
        git_repository=git_repository,
        pr_repository=pr_repository,
        config=config,
        pr_generation_service=pr_generation_service,
    )
