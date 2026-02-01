__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/9/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
from datetime import datetime
from logging import Logger
from typing import ClassVar, List, Optional

from langchain_core.language_models import LLM
from langchain_core.messages import HumanMessage
from langchain_core.outputs import Generation, LLMResult
from langchain_openai.chat_models.base import ChatOpenAI
from pydantic import Field

from agentfoundry.utils.config import Config

logger = logging.getLogger(__name__)


class OpenAILLM(LLM):
    """
    A generic OpenAILLM LLM class that interfaces with OpenAI's ChatCompletion API using
    LangChain's ChatOpenAI wrapper. This implementation delegates generation to ChatOpenAI,
    which uses the new API.
    """
    api_key: str = Field(..., description="Your OpenAILLM API key")
    model: str = Field(default="o3-mini", description="OpenAILLM model to use")
    logger: Logger = Field(default=None, description="Logger instance")
    chat_model: ChatOpenAI = Field(default=None, description="ChatOpenAI model instance")
    # Mark HumanMessage as a class variable, so Pydantic ignores it as a field.
    HumanMessage: ClassVar[type] = HumanMessage

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create an instance of ChatOpenAI with the proper parameters.
        self.chat_model = ChatOpenAI(model=self.model, **kwargs)
        logger.info("OpenAILLM initialized.")

    @property
    def _llm_type(self) -> str:
        """Return a string identifier for this LLM."""
        return "openai"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        logger.info(f"Calling OpenAILLM API with prompt: {prompt}")
        # If the prompt is a list, join the elements into a single string.
        if isinstance(prompt, list):
            prompt = "\n".join(prompt)
        # Prepare messages in the format required by ChatOpenAI.
        messages = [{"role": "user", "content": prompt}]
        try:
            result = self.chat_model.invoke(messages)
            return result.content.strip()
        except Exception as e:
            raise RuntimeError(f"Error calling OpenAILLM API: {e}")

    def generate(self, prompt: str, **kwargs) -> LLMResult:
        """
        Public interface to generate text.

        Args:
            prompt (str): The prompt to send.
            **kwargs: Additional keyword arguments.

        Returns:
            LLMResult: The generated result containing generations.
        """
        logger.info(f"Generating text with OpenAILLM model: {self.model}")
        start_time = datetime.now()
        text = self._call(prompt, **kwargs)
        logger.info(f"Text generated: {text}")
        logger.info(f"Generation completed in {str(datetime.now() - start_time)} seconds.")

        # Wrap the result text in a Generation object and then in an LLMResult.
        generation = Generation(text=text)

        return LLMResult(generations=[[generation]])


# Quick test when running this module directly
if __name__ == "__main__":
    key = Config().get("OPENAI_API_KEY")
    if not key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    # Use a supported model; adjust your configuration for "openai_model" as needed.
    llm_instance = OpenAILLM(api_key=key, model=Config().get("OPENAI_MODEL", "o3-mini"))
    output = llm_instance.generate("Who was the most famous Roman emperor?")
    print("Generated output:", output)
