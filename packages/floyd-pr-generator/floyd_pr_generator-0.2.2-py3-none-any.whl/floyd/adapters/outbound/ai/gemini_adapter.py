from floyd.adapters.outbound.ai.ai_adapter import AIAdapter
from floyd.application.dto.ai_config import AIConfig
from floyd.domain.entities.commit import Commit
from floyd.domain.entities.git_context import GitContext
from floyd.domain.entities.pull_request import PullRequest


class GeminiAdapter(AIAdapter):

    def _build_command(self, config: AIConfig) -> list[str]:
        command = ["gemini"]

        if config.model:
            command.extend(["--model", config.model])

        command.extend(["-p", "-"])
        return command

    def generate_pr(
        self,
        context: GitContext,
        config: AIConfig,
        feedback: str | None = None,
    ) -> PullRequest:
        prompt = self._build_pr_prompt(context, config, feedback)
        command = self._build_command(config)
        response = self.terminal.run(command, input_data=prompt, error_msg="Gemini CLI")
        return self._parse_response(response, context.current_branch.name)

    def generate_commit(
        self,
        diff: str,
        config: AIConfig,
        feedback: str | None = None,
    ) -> Commit:
        prompt = self._build_commit_prompt(diff, config, feedback)
        command = self._build_command(config)
        response = self.terminal.run(command, input_data=prompt, error_msg="Gemini CLI")
        return self._parse_commit_response(response)
