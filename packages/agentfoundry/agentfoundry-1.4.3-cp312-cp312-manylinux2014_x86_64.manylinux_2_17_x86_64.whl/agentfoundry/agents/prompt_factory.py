from typing import Dict, Tuple, Union, Callable, Any
from agentfoundry.agents.orchestrator import single_agent_prompt

class PromptFactory:
    """
    Manages base prompts on a per-(user_id,org_id,llm_model) key.
    Supports static strings, callable builders, or named prompt lookups.
    """

    _instance: "PromptFactory | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        # Value can be a static string or a (callable, kwargs) tuple
        self._prompts: Dict[Tuple[str, str, str], Union[str, Tuple[Callable, Dict[str, Any]]]] = {}
        self._initialized = True

    def get_prompt(self, user_id: str, org_id: str, llm_type: str) -> str:
        """
        Returns the resolved prompt for the given context.
        """
        key = (user_id, org_id, llm_type)
        stored = self._prompts.get(key)
        
        if stored is None:
            return single_agent_prompt
            
        if isinstance(stored, str):
            return stored
        
        if isinstance(stored, tuple):
            builder, kwargs = stored
            if callable(builder):
                return builder(**kwargs)
                
        return str(stored)

    def update_prompt(self,
                      user_id: str,
                      org_id: str,
                      llm_type: str,
                      prompt: Union[str, Callable[..., str]],
                      **kwargs) -> None:
        """
        Sets the base prompt for a given user/org/LLM.
        
        Args:
            prompt: Can be a static string OR a callable (like PromptRegistry.get_prompt).
            **kwargs: Arguments to pass to the callable (e.g., name='solicitation_parsing', schema=...).
        """
        key = (user_id, org_id, llm_type)
        
        if callable(prompt):
            self._prompts[key] = (prompt, kwargs)
        else:
            self._prompts[key] = prompt
