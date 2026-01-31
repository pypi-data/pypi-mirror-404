import sys

from floyd.adapters.inbound.cli import ui
from floyd.application.ports.inbound.pr_generation_port import PRGenerationPort
from floyd.application.ports.outbound.config_port import ConfigPort
from floyd.application.ports.outbound.git_repository_port import GitRepositoryPort
from floyd.domain.exceptions.domain_exception import DomainException
from floyd.domain.exceptions.git.invalid_branch_exception import InvalidBranchException
from floyd.domain.exceptions.git.branch_not_found_exception import (
    BranchNotFoundException,
)
from floyd.domain.exceptions.pr.pr_already_exist_exception import (
    PRAlreadyExistsException,
)
from floyd.domain.exceptions.pr.pr_generation_exception import PRGenerationException


class CLIAdapter:
    def __init__(
        self,
        pr_generation_service: PRGenerationPort,
        git_repository: GitRepositoryPort,
        config: ConfigPort,
    ) -> None:
        self._pr_service = pr_generation_service
        self._git_repository = git_repository
        self._config = config

    def run(self, args: list[str]) -> int:
        if len(args) < 1:
            ui.show_warning("Usage: floyd <pr|commit> [target-branch]")
            return 1

        if not self._git_repository.is_git_repo():
            ui.show_error("Error: This directory is not a git repository.")
            return 1

        ui.show_icon()

        ai_config = self._config.get_ai_config()
        ui.show_config(ai_config.provider.value, ai_config.model)

        mode = args[0].lower()

        try:
            if mode == "pr":
                if len(args) < 2:
                    ui.show_warning("Usage: floyd pr <target-branch>")
                    return 1
                ui.show_custom_instructions("PR", bool(ai_config.pr_instructions))
                return self._run_pr_workflow(args[1])
            elif mode == "commit":
                ui.show_custom_instructions("Commit", bool(ai_config.commit_instructions))
                return self._run_commit_workflow()
            else:
                ui.show_error(f"Unknown mode: {mode}. Use 'pr' or 'commit'.")
                return 1
        except KeyboardInterrupt:
            print("")
            ui.show_warning("Operation cancelled by user.")
            return 0

    def _run_pr_workflow(self, target_branch: str) -> int:
        current_branch = self._git_repository.get_current_branch()

        with ui.show_loading("Initializing workflow...") as status:
            try:
                status.update("[gray]Checking remote branches (network)...[/gray]")
                self._pr_service.validate_can_create_pr(current_branch, target_branch)

                status.update(
                    f"[gray]Fetching git diff against '{target_branch}'...[/gray]"
                )
                context = self._pr_service.get_git_context(target_branch)
            except InvalidBranchException as e:
                ui.show_warning(e.message)
                return 1
            except BranchNotFoundException as e:
                ui.show_error(
                    f"Error: The branch '{e.branch_name}' does not exist on origin."
                )
                return 1
            except PRAlreadyExistsException as e:
                ui.show_warning(
                    f"An open PR already exists for '{e.head_branch}' -> '{e.base_branch}'"
                )
                return 1

        if not context.has_changes():
            ui.show_warning("No changes found to create a PR.")
            return 1

        ui.show_info("Branch diff fetched successfully.")

        feedback: str | None = None

        while True:
            with ui.show_loading("Generating PR draft..."):
                try:
                    pr = self._pr_service.generate_pr_draft(context, feedback)
                    ui.show_info("PR draft created successfully.")
                except PRGenerationException as e:
                    ui.show_error(f"Failed to generate PR: {e.message}")
                    return 1
                except DomainException as e:
                    ui.show_error(e.message)
                    return 1

            ui.display_draft(pr)
            choice = ui.get_action_choice()

            if choice == "create":
                with ui.show_loading("Creating pull request..."):
                    try:
                        url = self._pr_service.create_pr(pr, target_branch)
                        if url:
                            ui.show_success("PR successfully created!")
                            ui.show_info(url)
                        else:
                            ui.show_error("Failed to create PR.")
                            return 1
                    except DomainException as e:
                        ui.show_error(f"Failed to create PR: {e.message}")
                        return 1
                break

            elif choice == "refine":
                feedback = ui.get_refinement_feedback()
                ui.show_info("Regenerating with your feedback...")
                continue

            else:
                ui.show_warning("Operation cancelled.")
                break

        return 0

    def _run_commit_workflow(self) -> int:
        diff = self._git_repository.get_staged_diff()

        if not diff or not diff.strip():
            ui.show_warning("No staged changes found. Use 'git add' to stage files first.")
            return 1

        ui.show_info("Staged changes detected.")
        feedback: str | None = None

        while True:
            with ui.show_loading("Generating commit message..."):
                try:
                    commit_draft = self._pr_service.generate_commit(diff, feedback)
                except PRGenerationException as e:
                    ui.show_error(f"Failed to generate commit: {e.message}")
                    return 1
                except DomainException as e:
                    ui.show_error(e.message)
                    return 1

            ui.display_commit_draft(commit_draft)
            choice = ui.get_commit_action_choice()

            if choice == "create":
                with ui.show_loading("Committing changes..."):
                    self._git_repository.commit(commit_draft)
                    ui.show_success("Changes committed successfully.")
                break
            elif choice == "refine":
                feedback = ui.get_refinement_feedback()
                ui.show_info("Regenerating with your feedback...")
                continue
            else:
                ui.show_warning("Commit cancelled.")
                break

        return 0


def main() -> None:
    from floyd.container import create_container

    try:
        container = create_container()

        cli = CLIAdapter(
            pr_generation_service=container.pr_generation_service,
            git_repository=container.git_repository,
            config=container.config,
        )

        sys.exit(cli.run(sys.argv[1:]))
    except DomainException as e:
        ui.show_error(e.message)

        sys.exit(1)
    except Exception as e:
        ui.show_error(f"An unexpected error occurred: {str(e)}")

        sys.exit(1)
