from abc import ABC, abstractmethod

from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest
from floyd.domain.entities.commit import Commit


class PRGenerationPort(ABC):

    @abstractmethod
    def generate_pr_draft(
        self,
        context: GitContext,
        feedback: str | None = None,
    ) -> PullRequest: ...

    @abstractmethod
    def create_pr(self, pr: PullRequest, base_branch: str) -> str: ...

    @abstractmethod
    def validate_can_create_pr(
        self, current_branch: str, target_branch: str
    ) -> None: ...

    @abstractmethod
    def get_git_context(self, target_branch: str) -> GitContext: ...

    @abstractmethod
    def generate_commit(self, diff: str, feedback: str | None = None) -> Commit: ...
