__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/9/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

from langchain import LLMChain, PromptTemplate

from agentfoundry.llm.llm_factory import LLMFactory
import logging


class GoalDecomposer:
    def __init__(self, llm):
        logger = logging.getLogger(__name__)
        self.logger.info("Initializing GoalDecomposer")
        self.llm = llm
        self.template = PromptTemplate(
            input_variables=["input_statement"],
            template=(
                "You are a planning assistant. Given the following input, "
                "extract a high-level goal and break it down into clear objectives. \n"
                "Input: {input_statement}\n\n"
                "Return a JSON object with keys 'goal' and 'objectives' (a list)."
            )
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.template)

    def decompose(self, input_statement: str) -> dict:
        self.logger.info(f"Decomposing goal from statement: {input_statement}")
        response = self.chain.run(input_statement=input_statement)
        self.logger.debug(f"Raw decomposition response: {response}")
        # Try to parse the response as JSON.
        import json
        try:
            result = json.loads(response)
        except Exception as e:
            self.logger.warning(f"Failed to parse decomposition JSON: {e}")
            result = {"goal": response, "objectives": []}
        self.logger.info(f"Decomposition result: {result}")
        return result


if __name__ == "__main__":
    # Example usage:
    llm = LLMFactory.get_llm_model()
    decomposer = GoalDecomposer(llm)
    input_statement = "I want to improve my health by exercising more and eating better."
    result = decomposer.decompose(input_statement)
    print(f"Decomposed Goal: {result.get('goal')}")
    print(f"Objectives: {result.get('objectives')}")
