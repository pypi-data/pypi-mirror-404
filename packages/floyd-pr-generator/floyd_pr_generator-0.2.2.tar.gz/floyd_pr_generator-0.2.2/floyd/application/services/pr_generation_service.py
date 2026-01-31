from floyd.application.ports.inbound.pr_generation_port import PRGenerationPort
from floyd.application.ports.outbound.ai_service_port import AIServicePort
from floyd.application.ports.outbound.config_port import ConfigPort
from floyd.application.ports.outbound.git_repository_port import GitRepositoryPort
from floyd.application.ports.outbound.pr_repository_port import PRRepositoryPort
from floyd.domain.entities.commit import Commit
from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest
from floyd.domain.exceptions.git.branch_not_found_exception import (
    BranchNotFoundException,
)
from floyd.domain.exceptions.git.invalid_branch_exception import InvalidBranchException
from floyd.domain.exceptions.pr.pr_already_exist_exception import (
    PRAlreadyExistsException,
)
from floyd.domain.value_objects.branch import Branch


class PRGenerationService(PRGenerationPort):

    def __init__(
        self,
        ai_service: AIServicePort,
        git_repository: GitRepositoryPort,
        pr_repository: PRRepositoryPort,
        config: ConfigPort,
    ) -> None:
        self._ai_service = ai_service
        self._git_repository = git_repository
        self._pr_repository = pr_repository
        self._config = config

    def validate_can_create_pr(self, current_branch: str, target_branch: str) -> None:
        if current_branch == target_branch:
            raise InvalidBranchException(
                f"Cannot create PR: source and target branch are the same ({current_branch})"
            )

        if not self._git_repository.branch_exists(target_branch):
            raise BranchNotFoundException(target_branch)

        if self._pr_repository.pr_exists(current_branch, target_branch):
            raise PRAlreadyExistsException(current_branch, target_branch)

    def get_git_context(self, target_branch: str) -> GitContext:
        self._git_repository.fetch()

        current_branch = self._git_repository.get_current_branch()
        commits = self._git_repository.get_commits(target_branch)
        diff = self._git_repository.get_diff(target_branch)
        diff_stat = self._git_repository.get_diff_stat(target_branch)

        return GitContext(
            current_branch=Branch(name=current_branch),
            target_branch=Branch(name=target_branch),
            commits=commits,
            diff=diff,
            diff_stat=diff_stat,
        )

    def generate_pr_draft(
        self,
        context: GitContext,
        feedback: str | None = None,
    ) -> PullRequest:
        ai_config = self._config.get_ai_config()
        return self._ai_service.generate_pr(context, ai_config, feedback)

    def generate_commit(
        self,
        diff: str,
        feedback: str | None = None,
    ) -> Commit:
        ai_config = self._config.get_ai_config()
        return self._ai_service.generate_commit(diff, ai_config, feedback)

    def create_pr(self, pr: PullRequest, base_branch: str) -> str:
        return self._pr_repository.create_pr(pr, base_branch)
