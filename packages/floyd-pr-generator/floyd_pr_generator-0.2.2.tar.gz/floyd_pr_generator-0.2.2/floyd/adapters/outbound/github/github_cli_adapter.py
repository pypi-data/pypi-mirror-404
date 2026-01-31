import os
import tempfile

from floyd.application.ports.outbound.pr_repository_port import PRRepositoryPort
from floyd.domain.entities.pull_request import PullRequest
from floyd.adapters.outbound.utils.terminal import Terminal


class GitHubCLIAdapter(PRRepositoryPort):

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def pr_exists(self, head_branch: str, base_branch: str) -> bool:
        result = self.terminal.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                head_branch,
                "--base",
                base_branch,
                "--state",
                "open",
                "--json",
                "number",
                "--jq",
                ".[0].number",
            ]
        )
        return bool(result)

    def create_pr(self, pr: PullRequest, base_branch: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".md", encoding="utf-8"
        ) as tf:
            tf.write(pr.body)
            temp_file_path = tf.name

        try:
            command = [
                "gh",
                "pr",
                "create",
                "--title",
                pr.title,
                "--body-file",
                temp_file_path,
                "--base",
                base_branch,
                "--head",
                pr.head_branch,
            ]

            return self.terminal.run(command, error_msg="GitHub CLI")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
