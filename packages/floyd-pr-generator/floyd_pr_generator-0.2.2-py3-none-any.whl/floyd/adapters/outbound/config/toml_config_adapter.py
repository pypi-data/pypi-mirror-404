import platform
import tomllib
from pathlib import Path

from floyd.application.dto.ai_config import AIConfig
from floyd.application.ports.outbound.config_port import ConfigPort
from floyd.domain.exceptions.ai.invalid_provider_exception import (
    InvalidProviderException,
)
from floyd.domain.exceptions.config.invalid_config_exception import (
    InvalidConfigException,
)
from floyd.domain.value_objects.ai_provider import AIProvider


class TomlConfigAdapter(ConfigPort):

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or self._get_default_config_path()

    def _get_default_config_path(self) -> Path:
        home = Path.home()
        system = platform.system()

        if system == "Windows":
            return home / "AppData" / "Roaming" / "floyd" / "floyd.toml"

        return home / ".config" / "floyd.toml"

    def get_ai_config(self) -> AIConfig:
        if not self._config_path.exists():
            raise InvalidConfigException(
                f"Configuration file not found at {self._config_path}. "
                "Please create it or check the path."
            )

        try:
            with open(self._config_path, "rb") as f:
                data = tomllib.load(f)

            ai_section = data.get("ai", {})

            raw_provider = str(ai_section.get("provider")).lower().strip()

            provider = AIProvider(name=raw_provider)

            model = str(ai_section.get("model") or "").strip()

            diff_limit_raw = ai_section.get("diff_limit")

            diff_limit = -1

            if diff_limit_raw is not None:
                try:
                    diff_limit = int(diff_limit_raw)
                except (ValueError, TypeError):
                    diff_limit = -1

            pr_instructions = str(ai_section.get("pr_instructions") or "").strip()
            commit_instructions = str(ai_section.get("commit_instructions") or "").strip()

            return AIConfig(
                provider=provider.type,
                model=model,
                diff_limit=diff_limit,
                pr_instructions=pr_instructions,
                commit_instructions=commit_instructions,
            )

        except InvalidProviderException as e:
            raise e
        except tomllib.TOMLDecodeError as e:
            raise InvalidConfigException(f"Failed to parse TOML file: {str(e)}")
        except Exception as e:
            raise InvalidConfigException(f"Configuration error: {str(e)}")
