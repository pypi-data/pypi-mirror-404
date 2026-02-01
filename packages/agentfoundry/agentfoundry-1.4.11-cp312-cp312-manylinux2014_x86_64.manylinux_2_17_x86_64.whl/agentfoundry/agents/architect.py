import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

logger = logging.getLogger(__name__)

class SubTask(BaseModel):
    id: str = Field(..., description="Unique identifier for the subtask (e.g., 'task_1')")
    description: str = Field(..., description="Description of what this subtask does")
    tool_names: List[str] = Field(..., description="List of exact tool names required for this subtask")
    system_prompt: str = Field(..., description="Specialized system prompt for the agent executing this subtask")
    depends_on: List[str] = Field(default_factory=list, description="List of task IDs that must complete before this one starts")

class ExecutionPlan(BaseModel):
    goal: str = Field(..., description="The overall goal of the execution plan")
    tasks: List[SubTask] = Field(..., description="List of subtasks to execute")

class AgentArchitect:
    """
    Analyzing user requests to generate execution plans with specialized agents.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=ExecutionPlan)
        
    def plan_task(self, task_description: str, available_tools_desc: str) -> ExecutionPlan:
        """
        Generates a structured execution plan for the given task.
        """
        logger.info(f"Architect planning task: {task_description[:60]}...")
        
        system_template = """You are an expert AI Agent Architect.
Your goal is to analyze a user request and break it down into a set of efficient subtasks.
For each subtask, you must:
1. Identify the specific tools needed from the available list.
2. Write a specialized system prompt for the sub-agent that will execute this task.
3. Determine dependencies to enable parallel execution where possible.

AVAILABLE TOOLS:
{tools_desc}

GUIDELINES:
- Be precise with tool names. Only use provided tools.
- Keep system prompts focused on the specific subtask.
- If a task depends on the output of another, list it in 'depends_on'.
- If tasks are independent, leave 'depends_on' empty to allow parallel execution.
- If the request is simple (single step), create a plan with just one task.

{format_instructions}
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", "{task}")
        ])
        
        formatted_prompt = prompt.format_messages(
            tools_desc=available_tools_desc,
            task=task_description,
            format_instructions=self.parser.get_format_instructions()
        )
        
        response = self.llm.invoke(formatted_prompt)
        try:
            plan = self.parser.parse(response.content)
            logger.info(f"Generated plan with {len(plan.tasks)} tasks")
            return plan
        except Exception as e:
            logger.error(f"Failed to parse execution plan: {e}")
            logger.debug(f"Raw response: {response.content}")
            raise e
