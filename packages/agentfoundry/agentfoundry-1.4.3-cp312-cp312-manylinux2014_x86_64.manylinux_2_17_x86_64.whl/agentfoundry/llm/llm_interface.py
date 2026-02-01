__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/8/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

# agentfoundry/llm/llm_interface.py

from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """
    Abstract base class for LLM services.

    Any LLM service implementation (local or cloud) must extend this interface
    and implement the required methods.
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text given a prompt.

        Args:
            prompt (str): The input prompt for the LLM.
            **kwargs: Additional parameters for generation.

        Returns:
            str: The generated text.
        """
        pass

    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        """
        Engage in a chat-like conversation with the LLM.

        Args:
            messages (list): A list representing the conversation history.
                             This can be a list of strings or dictionaries, depending on your design.
            **kwargs: Additional parameters for the chat.

        Returns:
            str: The LLM's response.
        """
        pass
