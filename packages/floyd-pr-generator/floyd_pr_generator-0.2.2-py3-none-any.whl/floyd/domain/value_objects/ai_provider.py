from enum import Enum

from pydantic import BaseModel, field_validator

from floyd.domain.exceptions.ai.invalid_provider_exception import (
    InvalidProviderException,
)


class ProviderType(str, Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    COPILOT = "copilot"


class AIProvider(BaseModel):
    name: str

    model_config = {"frozen": True}

    @property
    def type(self) -> ProviderType:
        return ProviderType(self.name)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip().lower()

        try:
            ProviderType(v)

            return v
        except ValueError:
            valid = [p.value for p in ProviderType]

            raise InvalidProviderException(
                f"Unsupported provider '{v}'. Supported: {', '.join(valid)}"
            )

    def is_claude(self) -> bool:
        return self.name == ProviderType.CLAUDE.value

    def is_gemini(self) -> bool:
        return self.name == ProviderType.GEMINI.value

    def is_copilot(self) -> bool:
        return self.name == ProviderType.COPILOT.value

    def __str__(self) -> str:
        return self.name
