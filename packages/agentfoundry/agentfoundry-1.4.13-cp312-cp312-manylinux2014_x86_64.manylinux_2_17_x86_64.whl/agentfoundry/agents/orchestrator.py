from __future__ import annotations

__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "6/14/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import os
import time
import uuid
import warnings
from typing import List, Tuple

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.prebuilt import create_react_agent as create_agent

from agentfoundry.agents.base_agent import BaseAgent
from agentfoundry.agents.memory.summary_utils import summarize_memory
from agentfoundry.agents.tools import memory_tools
from agentfoundry.llm.llm_factory import LLMFactory  # type: ignore
from agentfoundry.agents.architect import AgentArchitect, ExecutionPlan
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.utils.agent_config import AgentConfig

# Module logger for orchestrator internals
logger = logging.getLogger('agentfoundry.agents.orchestrator')

# Suppress Pydantic underscore-field warnings
warnings.filterwarnings("ignore", message="fields may not start with an underscore", category=RuntimeWarning)

single_agent_prompt = (
    "You are an AI Agent with access to a variety of tools, including memory, to assist the user.\n"
    "For each task, think first, which tool? what args?\n"
    "A task may require outputs and tool calls from multiple tools. Please be aware of which tools to use at each step, determine if another tool needs to be used.\n"
    "If a tool was created by the request of the user, then you can invoke that tool.\n"
    "\nMemory Usage and Tool Guidelines:\n"
    "- Store ephemeral chat turns in *thread_memory*.\n"
    "- Store personal prefs/emotions/values in *user_memory* (profile for key-value, facts for triples, semantic for text).\n"
    "- Store organization for organization-specific things like policies/compliance/organizational facts and info in *org_memory*.\n"
    "- Store general/vendor-neutral facts/docs that apply across users and organizations in *global_memory* only when not user/org-specific.\n"
    "- Summarize long text (>1K chars) before storing via summarize_any_memory.\n"
    "- Query appropriate memory level before responding; enforce security_level filters.\n"
    "- Keep k small on searches; prefer summaries for long contexts.\n"
    "- Delegate complex memory tasks to specialist agents (e.g., compliance_agent).\n"
    "- Store org/user/thread data in their respective memory tools; use global memory only for vendor-neutral or public facts. Do NOT store sensitive information in global memory.\n"
    "If the user asks for a new AI Tool, Python Tool, or Python code, delegate to the code_gen_agent (which owns the python_tool_creator tool) first, if possible.\n"
)

micropolicy_prompt = """
You are an expert in extracting compliance rules from text and return them exclusively as a valid JSON array. 

Each JSON object in the array MUST include these keys:
- "rule": (string) A short, concise title of the compliance rule.
- "description": (string) A clear, detailed explanation of the compliance rule.
- "value": (optional string) A specific numerical value or threshold explicitly mentioned in the rule.

JSON Example:
[{
"rule": "RSA encryption key length",
"description": "Minimum acceptable RSA encryption key length",
"value": "2048"
}]

STRICT REQUIREMENTS:
- You MUST respond ONLY with a valid JSON array.
- You MUST NOT include any summaries, commentary, explanations, or additional text outside the JSON structure.
- The description should be an actionable issue that can be used to CHECK if a rule is being enforced. For example, instead of "name a security officer", use something like "verify there is a named security officer"
"""

# Create a specialist agent
def make_specialist(name: str, tools: List[tool], llm, prompt: str | None = None):
    """ Create a specialist agent with the given name, tools, and LLM."""
    agent_name = " ".join(name.split("_")[:-1])
    tool_list_str = "\n".join(
        f"- {t.name}: {t.instruction}"
        for t in tools
    )
    if prompt is None:
        prompt = (
            f"You are a {agent_name} agent.\n\n"
            "AVAILABLE TOOLS:\n"
            f"{tool_list_str}\n\n"
            "INSTRUCTIONS:\n"
            "- Assist ONLY with tasks related to the agent, or tasks that can be fulfilled by the tools provided.\n"
            "- After you're done with your tasks, respond to the supervisor directly.\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        )
        if "SQL_database" in agent_name:
            prompt += "Do not assume or ask the user for the Database schema. First use a query to determine this."
    # Use LangGraph's in-memory checkpointer for thread-level state across steps.
    return create_agent(
        model=llm,
        tools=tools,
        prompt=prompt,
        name=name,
        checkpointer=MemorySaver(),
    )


# Orchestrator with a single supervisor and any number of specialist agents
class Orchestrator(BaseAgent):
    """
    Orchestrator orchestrates multiple specialist agents and manages memory tools.

    Singleton: constructing ``Orchestrator(...)`` anywhere returns the same
    shared instance. The first construction performs full initialization; later
    constructions are no-ops and return the existing instance, so call sites do
    not need to change.
    """

    _instance: "Orchestrator | None" = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_orchestrator(self, *, tools=None, prompt: str | None = None, name: str = "supervisor", checkpointer=None, llm=None) -> CompiledStateGraph:
        """Compile a LangGraph agent with the supplied tool set and prompt."""
        logger.info("Compiling supervisor with langchain.create_agent")
        return create_agent(
            model=llm or self.base_llm,
            tools=tools or self.master_tools,
            prompt=prompt or self.base_prompt,
            # Important: respect explicit checkpointer. If None, do NOT fall
            # back to self.memory – callers decide whether memory is desired.
            checkpointer=checkpointer,
            name=name,
        )

    def __init__(
        self,
        tool_registry: ToolRegistry,
        config: AgentConfig = None,
        llm=None,
        formatter_llm=None,
        base_prompt: str = None,
        # Deprecated parameters - kept for backward compatibility
        provider: str = None,
        llm_model: str = None,
    ):
        """
        Initialize the Orchestrator.

        Args:
            tool_registry: The registry containing available tools.
            config: AgentConfig object (required for new code).
            llm: Optional pre-configured LLM instance.
            base_prompt: Optional system prompt override.
            provider: DEPRECATED - use config.llm.provider instead.
            llm_model: DEPRECATED - use config.llm.model_name instead.
        """
        # Avoid trying to re-initialize the singleton on later calls
        if self.__class__._initialized:
            return
        super().__init__()
        # Initialize streaming cursor for supervisor responses to avoid AttributeError on first run.
        self.curr_counter = 0
        logger.info("Initializing Orchestrator")
        
        # Handle backward compatibility
        if config is None:
            warnings.warn(
                "Orchestrator() without config is deprecated. "
                "Pass AgentConfig explicitly.",
                DeprecationWarning,
                stacklevel=2
            )
            config = AgentConfig.from_legacy_config()
        
        if provider is not None or llm_model is not None:
            warnings.warn(
                "provider and llm_model parameters are deprecated. "
                "Set these in AgentConfig.llm instead.",
                DeprecationWarning,
                stacklevel=2
            )
        
        self.config = config
        logger.info(f"Using AgentConfig: provider={config.llm.provider}, model={config.llm.model_name}")
        
        # Set module-level config for memory tools
        memory_tools.set_module_config(config)
        
        self.registry = tool_registry
        
        # Auto-discovery of agent tools
        agent_tool_map = getattr(self.registry, "agent_tools", None)
        if not isinstance(agent_tool_map, dict):
            logger.info("Tool registry 'agent_tools' mapping missing. specific agent routing will be disabled, but tools will be available to the supervisor.")
            all_tools = []
            if hasattr(self.registry, "as_langchain_tools"):
                 all_tools = list(self.registry.as_langchain_tools())
            agent_tool_map = {
                "general_agent": all_tools,
                "memory_agent": [t for t in all_tools if "memory" in t.name]
            }
            self.registry.agent_tools = agent_tool_map

        logger.info(f"Agent tool map keys: {list(agent_tool_map.keys())}")
        
        # Base LLM/prompt and checkpoint memory for thread-level state
        self.base_prompt = base_prompt or single_agent_prompt
        
        # Determine LLM using the config object
        if llm:
            self.base_llm = llm
        else:
            # Pass the full config to the factory
            self.base_llm = LLMFactory.get_llm_model(
                config=self.config,
                provider=provider,  # Allow override for backward compat
                llm_model=llm_model,
            )
            
        # Formatter LLM for structured-output tasks (falls back to base_llm)
        if formatter_llm:
            self.formatter_llm = formatter_llm
        elif self.config.llm_formatter is not None:
            self.formatter_llm = LLMFactory.get_llm_by_role(config=self.config, role="formatting")
        else:
            self.formatter_llm = self.base_llm

        _fmt_name = getattr(self.formatter_llm, 'model_name', getattr(self.formatter_llm, 'model', ''))
        logger.info(f"Formatter LLM: {_fmt_name} (same_as_base={self.formatter_llm is self.base_llm})")

        # Store model name for logging
        self.llm_model = llm_model or self.config.llm.model_name
        
        self.architect = AgentArchitect(self.base_llm)
        self._mem_cache: dict[Tuple[str, str, str], Tuple[float, str]] = {}
        try:
            self._mem_ttl = int(os.getenv("AF_MEMORY_SUMMARY_TTL", "90"))
        except Exception:  # noqa
            self._mem_ttl = 90

        logger.info("Orchestrator initialized (Stateless Mode)")

        supervisor_tools = []
        if hasattr(self.registry, "as_langchain_tools"):
            try:
                supervisor_tools = list(self.registry.as_langchain_tools())
            except Exception:  # noqa
                supervisor_tools = []

        unique_tools = []
        seen_names = set()
        for t in supervisor_tools or []:
            n = getattr(t, "name", None)
            if n and n not in seen_names:
                seen_names.add(n)
                unique_tools.append(t)

        self.master_tools = unique_tools

        self._memory_tool_names = {
            "save_thread_memory", "search_thread_memory", "delete_thread_memory",
            "save_user_memory", "search_user_memory", "delete_user_memory",
            "save_org_memory", "search_org_memory", "delete_org_memory",
            "save_global_memory", "search_global_memory", "delete_global_memory",
            "summarize_any_memory",
        }
        self._non_memory_tools = [
            t for t in self.master_tools if getattr(t, "name", "") not in self._memory_tool_names
        ]

        self._no_memory_prompt = (
            "You are an AI Agent executing a single-turn task. "
            "Do not read, write, or summarize any memory. "
            "Rely only on the task content and non-memory tools. Keep responses concise."
        )

        try:
            self.supervisor = self.load_orchestrator(
                tools=self.master_tools,
                prompt=self.base_prompt,
                name="supervisor",
                checkpointer=MemorySaver(),
            )
        except Exception as err:
            self.supervisor = None
            logger.debug(f"Supervisor initialization skipped: {err}")

        self.__class__._initialized = True

        # Warm-up
        try:
            _ = self.base_llm
            from agentfoundry.vectorstores.factory import VectorStoreFactory
            
            # Pass explicit config to factory so it loads the correct provider (e.g. Milvus)
            prov = VectorStoreFactory.get_provider(config=self.config)
            
            try:
                prov.get_store(org_id=None)
                prov.get_store(org_id="global")
            except Exception:  # noqa
                pass
            try:
                if self.config:
                    default_org = self.config.org_id
                else:
                    from agentfoundry.utils.config import Config as _Cfg
                    default_org = str(_Cfg().get("ORG_ID", "") or "")
                    
                if default_org:
                    prov.get_store(org_id=default_org)
            except Exception:  # noqa
                pass
            try:
                from agentfoundry.kgraph.factory import KGraphFactory
                KGraphFactory.get_instance()
            except Exception:  # noqa
                pass
        except Exception as _warm_err:
            logger.debug(f"Warm-up encountered a non-fatal error: {_warm_err}")

    def _log_execution_details(self, response: dict, user_id: str, thread_id: str):
        """
        Log detailed tool usage and responses from a LangGraph execution.
        """
        messages = response.get("messages", [])
        for msg in messages:
            # Check for tool calls (AIMessage)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    args_str = str(tc.get('args', ''))
                    logger.info(f"[{user_id}:{thread_id}] Tool Call: {tc['name']} args={args_str[:200]}...")
            
            # Check for tool output (ToolMessage)
            if hasattr(msg, "type") and msg.type == "tool":
                content = str(msg.content)
                # Truncate output
                truncated = content[:500] + "..." if len(content) > 500 else content
                logger.info(f"[{user_id}:{thread_id}] Tool Output ({msg.name}): {truncated}")

            # Check for final answer (AIMessage without tool calls or just content)
            if hasattr(msg, "type") and msg.type == "ai" and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                logger.info(f"[{user_id}:{thread_id}] Agent Response: {str(msg.content)[:200]}...")

    def process_request(self, message: str | list, checkpointer=None, config: dict = None) -> str:
        """
        Process a user request using the Agent Architect to build and execute a dynamic plan.
        """
        if config is None:
            config = {"configurable": {"user_id": "default", "thread_id": "default"}}
            
        user_id = config.get("configurable", {}).get("user_id", "unknown")
        thread_id = config.get("configurable", {}).get("thread_id", "unknown")
        org_id = config.get("configurable", {}).get("org_id", "unknown")

        # 0. Build Memory Summary
        mem_summary = self._build_memory_summary(config)
            
        # 1. Get Tool Descriptions
        tools_desc = self.registry.inspect_tools()
        
        # 2. Architect Plan
        task_desc = message if isinstance(message, str) else str(message)
        # Handle list of messages (chat history)
        if isinstance(message, list):
            task_desc = str(message[-1].get("content", ""))

        logger.info(f"[{user_id}:{thread_id}] Processing Request (Org: {org_id}): {task_desc[:100]}...")

        try:
            plan = self.architect.plan_task(task_desc, tools_desc)
        except Exception as e:
            logger.error(f"[{user_id}:{thread_id}] Architect failed to plan: {e}")
            try:
                supervisor = create_agent(
                    model=self.base_llm,
                    tools=self.master_tools,
                    prompt=self.base_prompt,
                    checkpointer=checkpointer,
                    name="supervisor_fallback",
                )
                response = supervisor.invoke(
                    {"messages": self._coerce_task_messages(message)},
                    config=config,
                )
                self._log_execution_details(response, user_id, thread_id)
                return response["messages"][-1].content
            except Exception as fallback_err:
                logger.error(
                    f"[{user_id}:{thread_id}] Fallback supervisor failed: {fallback_err}"
                )
                return f"I encountered an error while planning the task: {e}"

        logger.info(f"[{user_id}:{thread_id}] Architect Plan: {plan.goal} ({len(plan.tasks)} tasks)")
        
        # 3. Execution
        # If single task, just create one agent and run.
        if len(plan.tasks) == 1:
            task = plan.tasks[0]
            tools = self.registry.get_tools_by_names(task.tool_names)
            if not tools and task.tool_names:
                logger.warning(f"[{user_id}:{thread_id}] Architect requested tools {task.tool_names} but none found. Using master tools.")
                tools = self.master_tools
            
            # Construct system prompt
            sys_prompt = f"{task.system_prompt}\n\nTask Goal: {task.description}"
            if mem_summary:
                sys_prompt += f"\n\nMEMORY CONTEXT:\n{mem_summary}"
            
            agent = create_agent(
                model=self.base_llm,
                tools=tools,
                prompt=sys_prompt,
                checkpointer=checkpointer
            )
            
            response = agent.invoke({"messages": [HumanMessage(content=task_desc)]}, config=config)
            self._log_execution_details(response, user_id, thread_id)
            return response["messages"][-1].content
            
        else:
            # Multi-step sequential execution
            context = f"Original Request: {task_desc}\n"
            if mem_summary:
                context += f"\nMEMORY CONTEXT:\n{mem_summary}\n"
                
            final_response = ""
            
            for task in plan.tasks:
                logger.info(f"[{user_id}:{thread_id}] Executing Subtask: {task.id} - {task.description}")
                tools = self.registry.get_tools_by_names(task.tool_names)
                if not tools and task.tool_names:
                    tools = self.master_tools

                sys_prompt = f"{task.system_prompt}\n\nYou are executing a subtask as part of a larger goal: {plan.goal}."
                
                agent = create_agent(
                    model=self.base_llm,
                    tools=tools,
                    prompt=sys_prompt,
                    checkpointer=checkpointer 
                )
                
                # Input to this agent is the task description + context
                agent_input = f"Task: {task.description}\n\nContext from previous steps:\n{context}"
                
                res = agent.invoke({"messages": [HumanMessage(content=agent_input)]}, config=config)
                self._log_execution_details(res, user_id, thread_id)
                output = res["messages"][-1].content
                
                context += f"\nOutput from {task.id}: {output}\n"
                final_response = output
                
            return final_response

    @classmethod
    def get_instance(cls, tool_registry: ToolRegistry | None = None, llm=None, llm_model=None, base_prompt: str | None = None, config: AgentConfig | None = None):
        if cls._instance is None:
            if tool_registry is None:
                raise ValueError("Orchestrator.get_instance requires tool_registry on first call")
            return cls(tool_registry, llm=llm, llm_model=llm_model, base_prompt=base_prompt, config=config)
        return cls._instance

    @staticmethod
    def create_agent(name: str, tools: List[tool], llm, prompt: str | None = None):
        """ Create a specialist agent with the given name, tools, and LLM."""
        agent_name = " ".join(name.split("_")[:-1])
        tool_list_str = "\n".join(
            f"- {t.name}: {t.instruction}"
            for t in tools
        )
        if prompt is None:
            prompt = (
                f"You are a {agent_name} agent.\n\n"
                "AVAILABLE TOOLS:\n"
                f"{tool_list_str}\n\n"
                "INSTRUCTIONS:\n"
                "- Assist ONLY with tasks related to the agent, or tasks that can be fulfilled by the tools provided.\n"
                "- After you're done with your tasks, respond to the supervisor directly.\n"
                "- Respond ONLY with the results of your work, do NOT include ANY other text."
            )
        # Use LangGraph's in-memory checkpointer for thread-level state across steps.
        return create_agent(
            model=llm,
            tools=tools,
            prompt=prompt,
            name=name,
            checkpointer=MemorySaver(),
        )

    @staticmethod
    def _content_to_text(content) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, (bytes, bytearray)):
            try:
                return content.decode("utf-8")
            except Exception:
                return content.decode("utf-8", errors="replace")
        if isinstance(content, (list, tuple)):
            parts: list[str] = []
            for seg in content:
                if isinstance(seg, dict):
                    if "text" in seg:
                        parts.append(str(seg.get("text") or ""))
                    elif "content" in seg:
                        parts.append(str(seg.get("content") or ""))
                    else:
                        parts.append(str(seg))
                else:
                    parts.append(str(seg))
            return "\n".join(p for p in parts if p)
        return str(content)

    @classmethod
    def _normalize_task_input(cls, task_input) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        if isinstance(task_input, (list, tuple)):
            for item in task_input:
                if isinstance(item, dict):
                    role = item.get("role", "user")
                    content = cls._content_to_text(item.get("content"))
                else:
                    role = "user"
                    content = cls._content_to_text(item)
                normalized.append({"role": str(role or "user"), "content": content})
        elif isinstance(task_input, dict):
            normalized.append({
                "role": str(task_input.get("role", "user") or "user"),
                "content": cls._content_to_text(task_input.get("content")),
            })
        else:
            normalized.append({"role": "user", "content": cls._content_to_text(task_input)})
        if not normalized:
            normalized = [{"role": "user", "content": ""}]
        return normalized

    @classmethod
    def _coerce_task_messages(cls, task_input) -> list:
        if (
            isinstance(task_input, list)
            and task_input
            and isinstance(task_input[0], dict)
            and "role" in task_input[0]
            and "content" in task_input[0]
        ):
            normalized = task_input
        else:
            normalized = cls._normalize_task_input(task_input)

        messages = []
        for item in normalized:
            role = (item.get("role") or "user").lower()
            content = item.get("content", "")
            if role == "system":
                messages.append(SystemMessage(content=content))
            elif role in {"assistant", "ai"}:
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        return messages or [HumanMessage(content="")]

    def _build_memory_summary(self, config: dict) -> str:
        if os.getenv("AF_DISABLE_MEMORY_SUMMARY", "false").lower() in ("1", "true", "yes", "on"):
            return ""
        cfg = config.get("configurable", {})
        uid = str(cfg.get("user_id", "") or "")
        tid = str(cfg.get("thread_id", "") or "")
        oid = str(cfg.get("org_id", "") or "")
        key = (uid, tid, oid)
        now = time.perf_counter()
        cached = self._mem_cache.get(key)
        if cached and (now - cached[0]) < self._mem_ttl:
            return cached[1]
        t0 = time.perf_counter()
        try:
            org_id_val = oid
            thread_sum = memory_tools.summarize_any_memory.invoke({
                "level": "thread",
                "config": {"configurable": {"user_id": uid, "thread_id": tid, "org_id": oid}},
            })
            combined_filter = {}
            ors = []
            if uid:
                ors.append({"user_id": uid})
            if org_id_val:
                ors.append({"org_id": org_id_val})
            if len(ors) > 1:
                combined_filter = {"$or": ors}
            elif len(ors) == 1:
                combined_filter = ors[0]
            base_sum = summarize_memory(combined_filter, org_id=org_id_val if org_id_val else None, max_tokens=8000)
            mem_summary = "\n".join(filter(None, [thread_sum, base_sum]))
        except Exception as _mem_err:
            mem_summary = ""
            logger.debug(f"Memory summarization failed: {_mem_err}")
        took_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(f"timing: memory_summary_ms={took_ms} uid={uid} tid={tid} oid={oid} len={len(mem_summary)}")
        self._mem_cache[key] = (now, mem_summary)
        return mem_summary

    def run_task(self, task: str | list | dict, *args, **kwargs):
        return_additional = kwargs.get('additional', False)
        use_memory: bool = kwargs.get('use_memory', False)
        allow_tools: bool = kwargs.get('allow_tools', False)
        allowed_tool_names: list[str] | None = kwargs.get('allowed_tool_names')
        model_role: str = kwargs.get('model_role', 'reasoning')
        config = kwargs.get('config') or {"configurable": {"user_id": "1", "thread_id": "1", "org_id": "NA", "security_level": "1"}}

        # Select LLM based on model_role
        active_llm = self.formatter_llm if model_role == "formatting" else self.base_llm

        normalized_messages = None
        task_preview = task if isinstance(task, str) else str(task)
        _active_model = getattr(active_llm, 'model_name', getattr(active_llm, 'model', type(active_llm).__name__))
        logger.info(
            "run_task invoked: additional=%s, use_memory=%s, model_role=%s, active_model=%s, task=%s",
            return_additional,
            use_memory,
            model_role,
            _active_model,
            task_preview[:60],
        )

        mem_summary = self._build_memory_summary(config) if use_memory else ""
        init_msgs = []
        if mem_summary:
            if len(mem_summary) > 400000:
                mem_summary = mem_summary[:400000]
            mem_summary_len = len(mem_summary)
            logger.info(f"run_task: use_memory: {use_memory} mem_summary_len={mem_summary_len} mem_cache_entries={len(self._mem_cache)}")
            init_msgs.append(SystemMessage(content=f"MEMORY_CONTEXT:\n{mem_summary}"))

        payload_for_messages = normalized_messages or self._normalize_task_input(task)
        init_msgs.extend(self._coerce_task_messages(payload_for_messages))

        init_payload_chars = 0
        for _msg in init_msgs:
            content = getattr(_msg, "content", "")
            if isinstance(content, (bytes, bytearray)):
                content = content.decode("utf-8", errors="replace")
            init_payload_chars += len(str(content))
        logger.info(
            "run_task: init_messages=%d init_payload_chars=%d task_chars=%d",
            len(init_msgs),
            init_payload_chars,
            len(task_preview),
        )

        init = {"messages": init_msgs}
        if not use_memory:
            tool_list = []
            if allow_tools:
                if isinstance(allowed_tool_names, (list, tuple)) and allowed_tool_names:
                    name_set = {str(n) for n in allowed_tool_names}
                    tool_list = [t for t in self._non_memory_tools if getattr(t, 'name', None) in name_set]
                else:
                    tool_list = list(self._non_memory_tools)
            supervisor = create_agent(
                model=active_llm,
                tools=tool_list,
                prompt=self._no_memory_prompt,
                checkpointer=None,
                name="NoMemorySupervisor",
            )
            _mn = getattr(active_llm, 'model_name', getattr(active_llm, 'model', type(active_llm).__name__))
            logger.info(f"run_task: using no-memory {_mn} supervisor with {len(tool_list)} tools (allow_tools={allow_tools}, model_role={model_role})")
        else:
            supervisor = self.load_orchestrator(
                tools=self.master_tools,
                prompt=self.base_prompt,
                name=f"supervisor_{uuid.uuid4().hex}",
                checkpointer=MemorySaver(),
                llm=active_llm,
            )
            logger.info(
                "run_task: using fresh supervisor with memory and %d tools (model_role=%s)",
                len(self.master_tools),
                model_role,
            )

        if supervisor is None:
            raise RuntimeError("Supervisor not initialized; cannot execute task")

        t_invoke = time.perf_counter()
        try:
            _t0 = time.perf_counter()
            responses = supervisor.invoke(init, config=config)  # noqa
            _dur_ms = (time.perf_counter() - _t0) * 1000.0
            reply = responses['messages'][-1].content
            if isinstance(reply, (bytes, bytearray)):
                reply = reply.decode("utf-8", errors="replace")
            else:
                reply = str(reply)
            logger.debug(f"Supervisor responses: {responses}")
        except Exception as e:
            logger.error(f"Exception in run_task for task '{task_preview[:60]}': {e}", exc_info=True)
            return f"An error occurred in the task: '{task_preview}': {str(e)}"
        response_messages = responses.get('messages', []) if isinstance(responses, dict) else []
        resp_payload_chars = 0
        tool_call_count = 0
        for _msg in response_messages:
            content = getattr(_msg, "content", "")
            if isinstance(content, (bytes, bytearray)):
                content = content.decode("utf-8", errors="replace")
            resp_payload_chars += len(str(content))
            extra = getattr(_msg, "additional_kwargs", {}) or {}
            tool_calls = extra.get('tool_calls')
            if isinstance(tool_calls, (list, tuple)):
                tool_call_count += len(tool_calls)
            elif tool_calls:
                tool_call_count += 1
        invoke_ms = int((time.perf_counter() - t_invoke) * 1000)
        logger.info(
            "timing: invoke_ms=%d task_chars=%d reply_chars=%d response_messages=%d response_payload_chars=%d tool_calls=%d",
            invoke_ms,
            len(task_preview),
            len(reply),
            len(response_messages),
            resp_payload_chars,
            tool_call_count,
        )
        if return_additional:
            return reply, responses
        if not hasattr(self, "curr_counter"):
            self.curr_counter = 0
        for i in range(self.curr_counter, len(responses['messages'])):
            inter = responses['messages'][i]
            if inter.content == "":
                if "tool_calls" in inter.additional_kwargs:
                    for tool_call in inter.additional_kwargs['tool_calls']:
                        logger.info(f"tool call: {tool_call['function']}")
            else:
                logger.debug(f"intermediate message: {str(responses['messages'][i].content).encode('utf-8')[:60]}...")
        self.curr_counter = len(responses['messages'])
        logger.info(f"run_task completed: reply: {reply[:120]}")
        return reply

    def chat(self, messages: list[dict], config: dict = None, additional: bool = False, checkpointer=None):
        logger.info(f"chat invoked: messages_count={len(messages)}, additional={additional}")
        if config is None:
            config = {"configurable": {"user_id": "1", "thread_id": "1", "org_id": "NA", "security_level": "1"}}
        
        if checkpointer is None:
            logger.warning("chat called without checkpointer. Creating temporary MemorySaver.")
            checkpointer = MemorySaver()

        # Extract content from messages or pass full list
        # process_request handles list extraction
        return self.process_request(messages, checkpointer=checkpointer, config=config)
