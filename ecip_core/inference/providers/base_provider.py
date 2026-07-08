from abc import ABC, abstractmethod
from typing import Callable
from ecip_core.inference.models.inference_response import InferenceResponse


class BaseProvider(ABC):
    """
    Abstract Base Class representing an inference backend provider.
    """

    @abstractmethod
    def generate(
        self,
        prompt_text: str,
        model_name: str,
        callback: Callable[[str], None] = None
    ) -> InferenceResponse:
        """
        Submits prompt to provider, normalizes output and execution metadata.
        If callback is provided, executes in token streaming mode.
        """
        pass

    @abstractmethod
    def validate_availability(self) -> bool:
        """
        Checks if the provider server is online and available.
        """
        pass
