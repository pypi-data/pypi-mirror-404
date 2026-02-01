__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/8/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

# agentfoundry/agents/base_agent.py

import logging
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Abstract base class for agents in AgentFoundry.

    Each agent should implement the run_task method to perform its designated operations.
    """

    def __init__(self, api_info: dict = None):
        """
        Initialize the agent.

        Args:
            api_info (dict, optional): A dictionary containing API-specific information.
                This can include API endpoint details, credentials, or any other metadata
                required by the agent.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_info = api_info or {}
        self.logger.info(f"{self.__class__.__name__} initialized with API info: {self.api_info}")

    @abstractmethod
    def run_task(self, task: str, *args, **kwargs):
        """
        Execute a specified task.

        This method must be implemented by all subclasses. The task parameter is expected to be
        a string identifier for the action the agent should perform. Additional arguments or keyword
        arguments can be passed to further specify the task details.

        Args:
            task (str): The task to be executed.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Any: The result of the task execution.
        """
        raise NotImplementedError("Subclasses must implement the run_task method.")

    @abstractmethod
    def chat(self, messages: list[dict], config: dict = None, additional: bool = False):
        """
        Multi-turn conversational interface using the supervisor pipeline.
        Args:
            messages: List of dicts with 'role' and 'content' keys representing the conversation history.
            config: Optional config dict for memory tools (user_id, thread_id, org_id, security_level).
            additional: If True, returns (response, full supervisor output).
        Returns:
            The assistant's reply, or (reply, full output) if additional=True.
        """

    def __str__(self):
        return f"{self.__class__.__name__}(api_info={self.api_info})"
