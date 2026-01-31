from abc import ABC, abstractmethod

from floyd.domain.entities.pull_request import PullRequest


class PRRepositoryPort(ABC):

    @abstractmethod
    def pr_exists(self, head_branch: str, base_branch: str) -> bool:
        ...

    @abstractmethod
    def create_pr(self, pr: PullRequest, base_branch: str) -> str:
        ...
