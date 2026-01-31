"""Domain exceptions."""

from floyd.domain.exceptions.ai.invalid_provider_exception import (
    InvalidProviderException,
)
from floyd.domain.exceptions.config.invalid_config_exception import (
    InvalidConfigException,
)
from floyd.domain.exceptions.domain_exception import DomainException
from floyd.domain.exceptions.git.branch_not_found_exception import (
    BranchNotFoundException,
)
from floyd.domain.exceptions.git.invalid_branch_exception import InvalidBranchException
from floyd.domain.exceptions.pr.pr_already_exist_exception import (
    PRAlreadyExistsException,
)
from floyd.domain.exceptions.pr.pr_generation_exception import PRGenerationException
from floyd.domain.exceptions.terminal.missing_dependency_exception import (
    MissingDependencyException,
)
from floyd.domain.exceptions.terminal.unexpected_exception import UnexpectedException

__all__ = [
    "BranchNotFoundException",
    "DomainException",
    "InvalidBranchException",
    "PRAlreadyExistsException",
    "PRGenerationException",
    "InvalidConfigException",
    "InvalidProviderException",
    "MissingDependencyException",
    "UnexpectedException",
]
