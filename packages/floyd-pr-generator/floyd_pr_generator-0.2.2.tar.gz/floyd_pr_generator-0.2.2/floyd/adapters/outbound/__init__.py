"""Outbound adapters (secondary/driven adapters)."""

from floyd.adapters.outbound.ai.claude_adapter import ClaudeAdapter
from floyd.adapters.outbound.config.toml_config_adapter import TomlConfigAdapter
from floyd.adapters.outbound.git.git_cli_adapter import GitCLIAdapter
from floyd.adapters.outbound.github.github_cli_adapter import GitHubCLIAdapter

__all__ = [
    "ClaudeAdapter",
    "GitCLIAdapter",
    "GitHubCLIAdapter",
    "TomlConfigAdapter",
]
