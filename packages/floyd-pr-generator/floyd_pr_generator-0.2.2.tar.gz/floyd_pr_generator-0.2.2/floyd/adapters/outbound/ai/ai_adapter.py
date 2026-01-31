from abc import ABC
from floyd.adapters.outbound.utils.terminal import Terminal
from floyd.application.dto.ai_config import AIConfig
from floyd.application.ports.outbound.ai_service_port import AIServicePort
from floyd.domain.entities.commit import Commit
from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest
from floyd.domain.exceptions.pr.pr_generation_exception import PRGenerationException
import re
from pathlib import Path


class AIAdapter(AIServicePort, ABC):

    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def _build_pr_prompt(
        self,
        context: GitContext,
        config: AIConfig,
        feedback: str | None = None,
    ) -> str:
        template_path = Path(__file__).parent / "prompt.txt"

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        diff = context.diff

        if config.diff_limit > 0 and len(diff) > config.diff_limit:
            diff = diff[:config.diff_limit] + "\n\n[... DIFF TRUNCATED ...]"

        instructions = f"\nUSER-SPECIFIC INSTRUCTIONS:\n{config.pr_instructions}" if config.pr_instructions else ""
        feedback_section = f"\nUSER FEEDBACK:\n{feedback}" if feedback else ""

        prompt = template.replace("{{current_branch}}", context.current_branch.name)
        prompt = prompt.replace("{{target_branch}}", context.target_branch.name)
        prompt = prompt.replace("{{commits}}", context.commits)
        prompt = prompt.replace("{{diff_stat}}", context.diff_stat)
        prompt = prompt.replace("{{instructions}}", instructions)
        prompt = prompt.replace("{{feedback}}", feedback_section)
        prompt = prompt.replace("{{diff}}", diff)

        return prompt

    def _build_commit_prompt(
        self,
        diff: str,
        config: AIConfig,
        feedback: str | None = None,
    ) -> str:
        template_path = Path(__file__).parent / "commit_prompt.txt"

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        if config.diff_limit > 0 and len(diff) > config.diff_limit:
            diff = diff[:config.diff_limit] + "\n\n[... DIFF TRUNCATED ...]"

        instructions = f"\nUSER-SPECIFIC INSTRUCTIONS:\n{config.commit_instructions}" if config.commit_instructions else ""
        feedback_section = f"\nUSER FEEDBACK:\n{feedback}" if feedback else ""

        prompt = template.replace("{{diff}}", diff)
        prompt = prompt.replace("{{instructions}}", instructions)
        prompt = prompt.replace("{{feedback}}", feedback_section)

        return prompt

    def _parse_response(self, response: str, head_branch: str) -> PullRequest:
        title, body = self._extract_title_body(response)
        return PullRequest(title=title, body=body, head_branch=head_branch)

    def _parse_commit_response(self, response: str) -> Commit:
        title, body = self._extract_title_body(response)
        return Commit(title=title, body=body)

    def _extract_title_body(self, response: str) -> tuple[str, str]:
        try:
            title_match = re.search(r"TITLE:\s*(.*)", response, re.IGNORECASE)
            body_match = re.search(r"BODY:\s*([\s\S]*)", response, re.IGNORECASE)

            if not title_match or not body_match:
                raise PRGenerationException("AI response missing title or body markers")

            title = title_match.group(1).split("BODY:")[0].strip()
            body = body_match.group(1).strip()

            return title, body
        except PRGenerationException:
            raise
        except Exception as e:
            raise PRGenerationException(f"Failed to parse AI response: {e}")
