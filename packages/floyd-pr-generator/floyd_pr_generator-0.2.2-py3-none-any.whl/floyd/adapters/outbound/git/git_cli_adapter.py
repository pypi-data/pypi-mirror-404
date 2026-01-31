from floyd.application.ports.outbound.git_repository_port import GitRepositoryPort
from floyd.adapters.outbound.utils.terminal import Terminal
from floyd.domain.entities.commit import Commit


class GitCLIAdapter(GitRepositoryPort):

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def fetch(self) -> None:
        self.terminal.run(
            ["git", "fetch", "origin", "--prune"],
            error_msg="Failed to sync with remote repository.",
        )

    def is_git_repo(self) -> bool:
        try:
            self.terminal.run(["git", "rev-parse", "--is-inside-work-tree"])
            return True
        except Exception:
            return False

    def branch_exists(self, branch_name: str) -> bool:
        try:
            self.terminal.run(
                ["git", "show-ref", "--verify", f"refs/remotes/origin/{branch_name}"]
            )
            return True
        except Exception:
            pass

        try:
            self.terminal.run(
                ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"]
            )
            return True
        except Exception:
            return False

    def get_current_branch(self) -> str:
        result = self.terminal.run(["git", "branch", "--show-current"])
        return result or ""

    def get_commits(self, base_branch: str) -> str:
        result = self.terminal.run(["git", "log", f"origin/{base_branch}..HEAD", "--oneline"])
        return result or ""

    def get_diff(self, base_branch: str) -> str:
        result = self.terminal.run(
            [
                "git",
                "diff",
                f"origin/{base_branch}..HEAD",
                ":!*.lock",
                ":!*-lock.json",
            ]
        )
        return result or ""

    def get_diff_stat(self, base_branch: str) -> str:
        result = self.terminal.run(
            [
                "git",
                "diff",
                "--stat",
                f"origin/{base_branch}..HEAD",
                ":!*.lock",
                ":!*-lock.json",
            ]
        )
        return result or ""

    def get_staged_diff(self) -> str:
        return self.terminal.run(["git", "diff", "--cached"])

    def commit(self, commit: Commit) -> str:
        command = ["git", "commit", "-m", commit.title]
        if commit.body:
            command.extend(["-m", commit.body])
        return self.terminal.run(command)




