"""Floyd - AI-powered pull request generator.

This package provides a CLI tool for generating pull requests using AI.

Hexagonal Architecture Layers:
- domain: Core business logic (entities, value objects, exceptions)
- application: Use cases and ports (interfaces)
- adapters: Infrastructure implementations (CLI, AI providers, git, etc.)
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("floyd")
except PackageNotFoundError:
    __version__ = "0.2.2"
