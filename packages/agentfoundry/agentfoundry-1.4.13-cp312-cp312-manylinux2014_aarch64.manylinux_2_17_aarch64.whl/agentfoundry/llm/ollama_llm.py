# agentfoundry/llm/ollama/ollama_llm.py
import logging
import sys
from typing import Mapping, Sequence, ClassVar, Callable

from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from .llm_interface import LLMInterface


class OllamaLLM(ChatOllama, LLMInterface):
    """ChatOllama that satisfies the LLMInterface and langgraph_supervisor's bind_tools requirement."""

    bind_tools: ClassVar[Callable]
    generate: ClassVar[Callable]
    chat: ClassVar[Callable]
    invoke: ClassVar[Callable]

    def bind_tools(           # minimal helper
        self,
        tools: Sequence[BaseTool],
        *args,
        **kwargs,
    ) -> "OllamaLLM":
        # A *shallow* copy is enough; comment it out if you’re OK mutating self.
        # from copy import copy
        # new = copy(self)

        new = self            # simply reuse the same instance
        new._tool_map: Mapping[str, BaseTool] = {t.name: t for t in tools}
        return new
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text given a prompt."""
        # Delegate to ChatOllama.invoke under the hood
        result = super().invoke([("human", prompt)], **kwargs)
        return getattr(result, "content", str(result))

    def chat(self, messages: list, **kwargs) -> str:
        """Engage in a chat-like conversation with the LLM."""
        result = super().invoke(messages, **kwargs)
        return getattr(result, "content", str(result))


# Quick test when running this module directly
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all log levels
    # Create handler that outputs to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    # Create a formatter and set it on the handler
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stdout_handler.setFormatter(formatter)
    # Add the handler to the logger
    logger.addHandler(stdout_handler)

    llm = OllamaLLM(model="gemma3:27b")
    messages = [{"role": "user", "content": "Write a short poem about the stars."}]
    output = llm.invoke(messages).content
    print("Output:\n", output)
