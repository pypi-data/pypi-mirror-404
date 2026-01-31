from abc import ABC, abstractmethod

from floyd.application.dto.ai_config import AIConfig


class ConfigPort(ABC):

    @abstractmethod
    def get_ai_config(self) -> AIConfig:
        ...
