__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/12/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

# Updated imports based on LangChain deprecations
from langchain_core.prompts import PromptTemplate
import logging


class PromptGenerator:
    """
    Generates code-related prompts using an LLM.

    This class provides methods to produce outputs for various code generation tasks,
    such as refactoring, documentation generation, summarization, and unit test creation.
    """

    def __init__(self, llm):
        """
        Initialize the PromptGenerator with a given LLM instance.

        Args:
            llm: An LLM instance that implements the invoke (and chat) methods.
        """
        logger = logging.getLogger(__name__)
        self.logger.info("Initializing PromptGenerator")
        self.llm = llm

        self.templates = {
            "refactor": PromptTemplate(
                input_variables=["code"],
                template=(
                    "You are an expert software engineer. Refactor the following code to improve "
                    "readability, performance, and maintainability while preserving its functionality.\n\n"
                    "Code:\n{code}\n\n"
                    "Refactored Code:"
                )
            ),
            "document": PromptTemplate(
                input_variables=["code"],
                template=(
                    "You are a technical writer. Generate comprehensive documentation for the following code. "
                    "Explain its functionality, inputs, outputs, and any potential edge cases.\n\n"
                    "Code:\n{code}\n\n"
                    "Documentation:"
                )
            ),
            "summarize": PromptTemplate(
                input_variables=["code"],
                template=(
                    "Summarize the functionality of the following code in a concise manner.\n\n"
                    "Code:\n{code}\n\n"
                    "Summary:"
                )
            ),
            "unit_tests": PromptTemplate(
                input_variables=["code"],
                template=(
                    "You are a software tester. Generate a set of unit tests for the following code. "
                    "Cover typical use cases, edge cases, and error handling scenarios.\n\n"
                    "Code:\n{code}\n\n"
                    "Unit Tests:"
                )
            )
        }

    def generate(self, task: str, code: str) -> str:
        """
        Generate output for a specified code generation task based on the provided code.

        Supported tasks:
            - "refactor": Refactor the code.
            - "document": Generate documentation for the code.
            - "summarize": Summarize the code.
            - "unit_tests": Generate unit tests for the code.

        Args:
            task (str): The code generation task.
            code (str): The code snippet to process.

        Returns:
            str: The generated output from the LLM.
        """
        self.logger.info(f"Generating prompt for task: {task}")
        if task not in self.templates:
            self.logger.error(f"Unsupported task '{task}' requested")
            raise ValueError(f"Unsupported task '{task}'. Supported tasks are: {list(self.templates.keys())}")
        chain = self.templates[task] | self.llm
        result = chain.invoke({"code": code}).content.strip()
        self.logger.debug(f"PromptGenerator result for task '{task}': {result}")
        return result


if __name__ == "__main__":
    # Use LLMFactory to get a real LLM instance.
    from agentfoundry.llm.llm_factory import LLMFactory

    llm_instance = LLMFactory.get_llm_model()
    prompt_gen = PromptGenerator(llm_instance)

    sample_code = "def add(a, b):\n    return a + b"

    print("=== Refactored Code ===")
    print(prompt_gen.generate("refactor", sample_code))
    print("\n=== Documentation ===")
    print(prompt_gen.generate("document", sample_code))
    print("\n=== Summary ===")
    print(prompt_gen.generate("summarize", sample_code))
    print("\n=== Unit Tests ===")
    print(prompt_gen.generate("unit_tests", sample_code))
