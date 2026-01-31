import subprocess
import shutil
import platform
import shlex
from rich.console import Console

from floyd.domain.exceptions.terminal.missing_dependency_exception import (
    MissingDependencyException,
)
from floyd.domain.exceptions.terminal.unexpected_exception import UnexpectedException


class Terminal:
    def __init__(self) -> None:
        self.console = Console()
        self._is_windows = platform.system() == "Windows"

    def is_installed(self, tool: str) -> bool:
        return shutil.which(tool) is not None

    def ensure_installed(self, tool: str) -> None:
        if not self.is_installed(tool):
            raise MissingDependencyException(tool)

    def run(
        self,
        command: list[str] | str,
        input_data: str | None = None,
        error_msg: str = "Command Failed",
    ) -> str:
        if isinstance(command, str):
            cmd_list = command if self._is_windows else shlex.split(command)
        else:
            cmd_list = command

        try:
            result = subprocess.run(
                cmd_list,
                input=input_data,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                shell=self._is_windows,
            )

            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            detail = e.stderr.strip() or str(e)
            raise UnexpectedException(f"{error_msg}: {detail}") from None

        except FileNotFoundError:
            cmd_name = (
                cmd_list[0] if isinstance(cmd_list, list) else cmd_list.split()[0]
            )
            raise MissingDependencyException(cmd_name)
