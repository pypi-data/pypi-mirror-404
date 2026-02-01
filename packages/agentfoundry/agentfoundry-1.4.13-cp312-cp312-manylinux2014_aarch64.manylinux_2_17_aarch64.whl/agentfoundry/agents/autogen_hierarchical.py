"""Hierarchical AutoGen orchestrator integrated with LangGraph utilities."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # pragma: no cover - dependency injection validated in tests
    from autogen import AssistantAgent, UserProxyAgent
except ImportError as exc:  # pragma: no cover - surfaced during runtime configuration
    raise ImportError(
        "AutoGen is required for the hierarchical orchestrator."
        " Install `autogen-agentchat`>=0.2.36."
    ) from exc

from langchain_core.tools import BaseTool

from agentfoundry.agents.base_agent import BaseAgent
from agentfoundry.agents.memory.global_memory import GlobalMemory
from agentfoundry.agents.memory.org_memory import OrgMemory
from agentfoundry.agents.memory.summary_utils import summarize_memory
from agentfoundry.agents.memory.thread_memory import ThreadMemory
from agentfoundry.agents.memory.user_memory import UserMemory
from agentfoundry.kgraph.factory import KGraphFactory
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.utils.config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper data containers
# ---------------------------------------------------------------------------


def _default_config() -> Config:
    # Lazy load config to avoid repeated disk reads
    return Config()


def _safe_json_loads(candidate: str) -> Any:
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        cleaned = candidate.strip()
        # Simple guard for trailing fenced code-blocks
        cleaned = re.sub(r"^```json|```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None


def _ensure_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _tool_signature(name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


@dataclass
class ToolBinding:
    """Adapt LangChain tools so AutoGen agents can call them."""

    tool: BaseTool
    config_factory: Callable[[], Dict[str, Any]]

    def as_callable(self) -> Callable[..., Any]:
        def _callable(**kwargs: Any) -> Any:
            payload: Dict[str, Any]
            if kwargs:
                payload = dict(kwargs)
            else:
                payload = {}

            requires_config = False
            if getattr(self.tool, "args_schema", None):
                schema = getattr(self.tool.args_schema, "schema", None)
                if callable(schema):
                    try:
                        tool_schema = schema()
                        if isinstance(tool_schema, dict):
                            requires_config = "config" in tool_schema.get("properties", {})
                    except Exception:  # pragma: no cover - defensive
                        requires_config = False

            if requires_config and "config" not in payload:
                payload["config"] = self.config_factory()

            try:
                return self.tool.invoke(payload)
            except Exception as exc:  # pragma: no cover - provide readable error upstream
                logger.warning("Tool '%s' invocation failed: %s", self.tool.name, exc, exc_info=True)
                raise

        _callable.__name__ = self.tool.name
        _callable.__doc__ = self.tool.description or self.tool.name
        return _callable

    def signature(self) -> Dict[str, Any]:
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        if getattr(self.tool, "args_schema", None):
            schema_func = getattr(self.tool.args_schema, "schema", None)
            if callable(schema_func):
                try:
                    schema = schema_func()
                except Exception:  # pragma: no cover - fallback to default schema
                    logger.debug("Falling back to default schema for tool %s", self.tool.name)
        return {
            "type": "function",
            "function": {
                "name": self.tool.name,
                "description": self.tool.description or self.tool.name,
                "parameters": schema,
            },
        }


@dataclass
class MemoryToolset:
    user_id: str
    thread_id: str
    org_id: str
    security_level: Optional[str] = None

    _thread_mem: Optional[ThreadMemory] = field(default=None, init=False, repr=False)
    _user_mem: Optional[UserMemory] = field(default=None, init=False, repr=False)
    _org_mem: Optional[OrgMemory] = field(default=None, init=False, repr=False)
    _global_mem: Optional[GlobalMemory] = field(default=None, init=False, repr=False)

    def _thread(self) -> ThreadMemory:
        if self._thread_mem is None:
            self._thread_mem = ThreadMemory(user_id=self.user_id, thread_id=self.thread_id, org_id=self.org_id)
        return self._thread_mem

    def _user(self) -> UserMemory:
        if self._user_mem is None:
            self._user_mem = UserMemory(self.user_id, org_id=self.org_id)
        return self._user_mem

    def _org(self) -> OrgMemory:
        if self._org_mem is None:
            self._org_mem = OrgMemory(self.org_id)
        return self._org_mem

    def _global(self) -> GlobalMemory:
        if self._global_mem is None:
            self._global_mem = GlobalMemory()
        return self._global_mem

    # Thread memory -----------------------------------------------------
    def save_thread(self, text: str) -> str:
        self._thread().add(text)
        return "thread memory saved"

    def search_thread(self, query: str, k: int = 5) -> List[str]:
        return self._thread().similarity_search(query, k)

    def clear_thread(self) -> str:
        self._thread().clear()
        return "thread memory cleared"

    # User memory -------------------------------------------------------
    def save_user(self, text: str, *, role_level: int = 0) -> str:
        self._user().add_semantic_item(text, role_level=role_level)
        return "user memory saved"

    def search_user(self, query: str, k: int = 5) -> List[str]:
        return self._user().semantic_search(query, k=k)

    # Org memory --------------------------------------------------------
    def save_org(self, text: str) -> str:
        self._org().add_semantic_item(text)
        return "org memory saved"

    def search_org(self, query: str, k: int = 5) -> List[str]:
        return self._org().semantic_search(query, k=k)

    # Global memory -----------------------------------------------------
    def save_global(self, text: str) -> str:
        self._global().add_document(text)
        return "global memory saved"

    def search_global(self, query: str, k: int = 5) -> List[str]:
        return self._global().search(query, k)


@dataclass
class KnowledgeGraphToolset:
    user_id: str
    org_id: str
    factory: KGraphFactory = field(default_factory=KGraphFactory.get_instance, repr=False)

    def _graph(self):
        return self.factory.get_kgraph()

    def upsert_fact(self, subject: str, predicate: str, obj: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        metadata = metadata or {}
        metadata.setdefault("user_id", self.user_id)
        metadata.setdefault("org_id", self.org_id)
        return self._graph().upsert_fact(subject, predicate, obj, metadata)

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._graph().search(query, user_id=self.user_id, org_id=self.org_id, k=k)

    def neighbours(self, entity: str, depth: int = 2) -> List[Dict[str, Any]]:
        depth = max(1, min(depth, 5))
        return self._graph().get_neighbours(entity, depth=depth)


@dataclass
class SpecialistAgent:
    """Wrapper combining an AutoGen assistant with a dedicated controller."""

    name: str
    role: str
    agent: AssistantAgent
    controller: UserProxyAgent
    tool_signatures: List[Dict[str, Any]] = field(default_factory=list)

    async def run(
        self,
        instruction: str,
        *,
        silent: bool = True,
        summary_method: str = "last_msg",
        max_turns: int = 1,
    ) -> Tuple[str, Dict[str, Any]]:
        result = await self.controller.a_initiate_chat(
            self.agent,
            message=instruction,
            silent=silent,
            summary_method=summary_method,
            max_turns=max_turns,
        )
        summary = result.summary.strip()
        if not summary and result.chat_history:
            for entry in reversed(result.chat_history):
                role = entry.get("role") if isinstance(entry, dict) else None
                content = entry.get("content") if isinstance(entry, dict) else None
                if role in {"assistant", "tool"} and content:
                    summary = str(content).strip()
                    if summary:
                        break
        if not summary:
            default_reply = getattr(self.agent, "default_auto_reply", None)
            if isinstance(default_reply, str) and default_reply:
                summary = default_reply
        return summary, {
            "chat_id": result.chat_id,
            "history": result.chat_history,
            "human_inputs": result.human_input,
        }


class HierarchicalAutoGenOrchestrator(BaseAgent):
    """AutoGen-based orchestrator coordinating hierarchical specialist agents."""

    PLAN_PROMPT = (
        "You are the lead coordinator for AgentFoundry.\n"
        "Summarise the user's objective, then break it into four stages: data_retrieval, data_processing, decision_making, output_generation.\n"
        "Return a compact JSON object with keys 'data_retrieval', 'data_processing', 'decision_making', 'output_generation'.\n"
        "Each value must be an object containing 'goal' and 'inputs'.\n"
        "The 'inputs' value should be a short natural-language string combining relevant context.\n"
        "If additional loops are needed, describe them under an optional 'notes' field."
    )

    def __init__(
        self,
        tool_registry: ToolRegistry,
        *,
        llm_config: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        max_tools_per_agent: int = 10,
    ) -> None:
        super().__init__()
        self.registry = tool_registry
        self.max_tools_per_agent = max(1, max_tools_per_agent)
        self.config = _default_config()
        self.llm_config = self._resolve_llm_config(llm_config, provider, llm_model)
        self._orchestrator_agent: Optional[AssistantAgent] = None
        self._orchestrator_controller: Optional[UserProxyAgent] = None
        self.specialists: Dict[str, SpecialistAgent] = {}
        self._tool_bindings: Dict[str, List[ToolBinding]] = {}
        self._current_identity: Dict[str, str] = {
            "user_id": "system",
            "thread_id": "shared",
            "org_id": self.config.get("ORG_ID", "default"),
            "security_level": "system",
        }
        self._setup_agents()

    # ------------------------------------------------------------------
    # BaseAgent API
    # ------------------------------------------------------------------
    def run_task(self, task: str, *args, **kwargs):  # type: ignore[override]
        config = kwargs.get("config")
        coro = self._execute_workflow(task, config=config)
        loop = _ensure_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        return loop.run_until_complete(coro)

    def chat(self, messages: List[Dict[str, Any]], config: Dict[str, Any] | None = None, additional: bool = False):  # type: ignore[override]
        user_message = messages[-1]["content"] if messages else ""
        coro = self._execute_workflow(user_message, config=config, additional=additional)
        loop = _ensure_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        return loop.run_until_complete(coro)

    # ------------------------------------------------------------------
    # Internal orchestration
    # ------------------------------------------------------------------
    def _build_llm_config(self, *, provider: Optional[str], model_name: Optional[str]) -> Dict[str, Any]:
        provider = provider or self.config.get("LLM_PROVIDER", "openai").lower()
        if provider == "openai":
            api_key = self.config.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for AutoGen OpenAI configuration.")
            model = model_name or self.config.get("OPENAI_MODEL", "gpt-4o-mini")
            base_url = self.config.get("OPENAI_BASE_URL", "")
            config_entry = {"model": model, "api_key": api_key}
            if base_url:
                config_entry["api_base"] = base_url
            llm_config = {"config_list": [config_entry], "timeout": int(self.config.get("LLM_TIMEOUT", 120))}
            return llm_config
        if provider == "ollama":
            host = self.config.get("OLLAMA.HOST", "http://127.0.0.1:11434")
            model = model_name or self.config.get("OLLAMA.MODEL", "gemma2:9b")
            return {"config_list": [{"model": model, "base_url": host, "provider": "ollama"}]}
        raise ValueError(f"Unsupported AutoGen provider '{provider}'. Provide llm_config explicitly.")

    def _resolve_llm_config(
        self,
        provided: Optional[Dict[str, Any] | bool],
        provider: Optional[str],
        model_name: Optional[str],
    ) -> Dict[str, Any] | bool:
        if provided is False:
            return False
        if isinstance(provided, dict):
            return provided
        return self._build_llm_config(provider=provider, model_name=model_name)

    def _setup_agents(self) -> None:
        orchestrator_prompt = (
            "You are the AgentFoundry orchestrator. Coordinate specialists using memory and knowledge graph tools."
        )
        self._orchestrator_agent = AssistantAgent(
            name="orchestrator",
            llm_config=self.llm_config,
            system_message=orchestrator_prompt,
        )
        self._orchestrator_controller = UserProxyAgent(
            name="workflow_controller",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False},
        )

        base_specs = [
            ("data_retrieval", "Collect data from tools, search, and memory for downstream processing."),
            ("data_processing", "Clean and transform retrieved data into structured insights."),
            ("decision_making", "Prioritise actions leveraging memory, knowledge graph, and current goals."),
            ("output_generation", "Assemble a final report or user-facing response summarising all outcomes."),
        ]

        self._tool_bindings = self._allocate_tools()

        for name, role_description in base_specs:
            agent = AssistantAgent(
                name=name,
                llm_config=self.llm_config,
                system_message=role_description,
            )
            controller = UserProxyAgent(
                name=f"{name}_controller",
                human_input_mode="NEVER",
                code_execution_config={"use_docker": False},
            )

            bindings = self._tool_bindings.get(name, [])
            if bindings:
                register_map = {binding.tool.name: binding.as_callable() for binding in bindings}
                agent.register_function(register_map)
                tool_sigs = [binding.signature() for binding in bindings]
                if agent.llm_config:
                    for sig in tool_sigs:
                        agent.update_tool_signature(sig, is_remove=None)
            else:
                tool_sigs = []

            self.specialists[name] = SpecialistAgent(
                name=name,
                role=role_description,
                agent=agent,
                controller=controller,
                tool_signatures=tool_sigs,
            )

    def _allocate_tools(self) -> Dict[str, List[ToolBinding]]:
        langchain_tools = list(self.registry.as_langchain_tools())
        if not langchain_tools:
            return {
                "data_retrieval": [],
                "data_processing": [],
                "decision_making": [],
                "output_generation": [],
            }

        keywords = {
            "data_retrieval": ["search", "fetch", "http", "web", "query", "scrape", "vector"],
            "data_processing": ["process", "clean", "summarize", "python", "pandas", "transform"],
            "decision_making": ["plan", "decision", "memory", "graph", "priorit", "evaluate"],
            "output_generation": ["report", "write", "generate", "pdf", "render", "notify"],
        }

        def _bucket(tool: BaseTool) -> str:
            name = (tool.name or "").lower()
            description = (tool.description or "").lower()
            for bucket, cues in keywords.items():
                if any(cue in name or cue in description for cue in cues):
                    return bucket
            counts = {bucket: len(bindings) for bucket, bindings in allocation.items()}
            return min(counts, key=counts.get)

        allocation: Dict[str, List[ToolBinding]] = {
            "data_retrieval": [],
            "data_processing": [],
            "decision_making": [],
            "output_generation": [],
        }

        for tool in langchain_tools:
            bucket = _bucket(tool)
            if len(allocation[bucket]) >= self.max_tools_per_agent:
                # Overflow: push to smallest current bucket regardless of keyword match
                bucket = min(allocation, key=lambda key: len(allocation[key]))
            allocation[bucket].append(ToolBinding(tool=tool, config_factory=self._tool_config_payload))

        return allocation

    def _tool_config_payload(self) -> Dict[str, Any]:
        return {"configurable": dict(self._current_identity)}

    async def _execute_workflow(self, user_message: str, *, config: Optional[Dict[str, Any]] = None, additional: bool = False) -> Any:
        resolved = self._resolve_identity(config)
        self._current_identity = dict(resolved)
        memory_tools = MemoryToolset(
            resolved["user_id"],
            resolved["thread_id"],
            resolved["org_id"],
            resolved.get("security_level"),
        )
        knowledge_tools = KnowledgeGraphToolset(resolved["user_id"], resolved["org_id"])

        plan = await self._plan_workflow(user_message, resolved, memory_tools, knowledge_tools)
        execution_log: Dict[str, Any] = {"plan": plan, "stages": {}}

        data_runtime = self._inject_runtime_tools(
            self.specialists["data_retrieval"],
            "data_retrieval",
            memory_tools,
            knowledge_tools,
        )
        data_result, data_meta = await self.specialists["data_retrieval"].run(
            self._format_agent_instruction(
                "data_retrieval",
                plan,
                user_message,
                resolved,
                extra_inputs={"memory_summary": self._memory_summary(resolved)},
            )
        )
        self._clear_runtime_tools(self.specialists["data_retrieval"], data_runtime)
        execution_log["stages"]["data_retrieval"] = {"output": data_result, "meta": data_meta}

        processing_input = {
            "upstream": data_result,
            "user_request": user_message,
            "notes": plan.get("notes", ""),
        }
        processing_runtime = self._inject_runtime_tools(
            self.specialists["data_processing"],
            "data_processing",
            memory_tools,
            knowledge_tools,
        )
        processing_result, processing_meta = await self.specialists["data_processing"].run(
            self._format_agent_instruction(
                "data_processing",
                plan,
                user_message,
                resolved,
                extra_inputs=processing_input,
            )
        )
        self._clear_runtime_tools(self.specialists["data_processing"], processing_runtime)
        execution_log["stages"]["data_processing"] = {"output": processing_result, "meta": processing_meta}

        decision_input = {
            "processed": processing_result,
            "memory_reference": memory_tools.search_user(user_message, k=3) if user_message else [],
            "knowledge_graph": knowledge_tools.search(user_message, k=3) if user_message else [],
        }
        decision_runtime = self._inject_runtime_tools(
            self.specialists["decision_making"],
            "decision_making",
            memory_tools,
            knowledge_tools,
        )
        decision_result, decision_meta = await self.specialists["decision_making"].run(
            self._format_agent_instruction(
                "decision_making",
                plan,
                user_message,
                resolved,
                extra_inputs=decision_input,
            )
        )
        self._clear_runtime_tools(self.specialists["decision_making"], decision_runtime)
        execution_log["stages"]["decision_making"] = {"output": decision_result, "meta": decision_meta}

        output_payload = {
            "decisions": decision_result,
            "processed": processing_result,
            "retrieved": data_result,
            "identity": resolved,
        }
        output_runtime = self._inject_runtime_tools(
            self.specialists["output_generation"],
            "output_generation",
            memory_tools,
            knowledge_tools,
        )
        output_result, output_meta = await self.specialists["output_generation"].run(
            self._format_agent_instruction(
                "output_generation",
                plan,
                user_message,
                resolved,
                extra_inputs=output_payload,
            ),
            summary_method="last_msg",
        )
        self._clear_runtime_tools(self.specialists["output_generation"], output_runtime)
        execution_log["stages"]["output_generation"] = {"output": output_result, "meta": output_meta}

        if additional:
            return output_result, execution_log
        return output_result

    async def _plan_workflow(
        self,
        user_message: str,
        identity: Dict[str, str],
        memory_tools: MemoryToolset,
        knowledge_tools: KnowledgeGraphToolset,
    ) -> Dict[str, Any]:
        orchestrator = self._orchestrator_agent
        controller = self._orchestrator_controller
        if orchestrator is None or controller is None:
            raise RuntimeError("Orchestrator agents not initialised")

        memory_summary = self._memory_summary(identity)
        kg_preview = knowledge_tools.search(user_message, k=2) if user_message else []
        seed_context = {
            "user": user_message,
            "identity": identity,
            "memory": memory_summary,
            "knowledge_graph": kg_preview,
        }
        prompt = (
            f"{self.PLAN_PROMPT}\nCurrent context:\n"
            f"- Identity: {json.dumps(identity)}\n"
            f"- Memory summary: {memory_summary[:800]}\n"
            f"- Knowledge graph hits: {json.dumps(kg_preview)[:800]}\n"
            f"- User request: {user_message}"
        )

        try:
            result = await controller.a_initiate_chat(
                orchestrator,
                message=prompt,
                summary_method="last_msg",
                silent=True,
                max_turns=1,
            )
            candidate = result.summary.strip()
            parsed = _safe_json_loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            logger.warning("Planner returned non-JSON output; falling back to template. Output: %s", candidate)
        except Exception as exc:  # pragma: no cover - ensures robustness without API key
            logger.warning("Planner failed; using fallback plan. Error: %s", exc)

        return {
            "data_retrieval": {
                "goal": "Collect raw data relevant to the user request.",
                "inputs": user_message,
            },
            "data_processing": {
                "goal": "Normalise and clean the collected data, highlighting anomalies.",
                "inputs": "Use results from data retrieval.",
            },
            "decision_making": {
                "goal": "Evaluate processed insights and prioritise recommended actions.",
                "inputs": "Combine processed data with memory/knowledge graph context.",
            },
            "output_generation": {
                "goal": "Produce a concise narrative report with actionable steps.",
                "inputs": "Summarise decisions and cite supporting data.",
            },
            "notes": "Fallback plan due to planner failure.",
        }

    def _format_agent_instruction(
        self,
        role: str,
        plan: Dict[str, Any],
        user_message: str,
        identity: Dict[str, str],
        *,
        extra_inputs: Optional[Dict[str, Any]] = None,
    ) -> str:
        plan_entry = plan.get(role, {})
        goal = plan_entry.get("goal", "Execute your specialist task")
        inputs = plan_entry.get("inputs", "")
        notes = plan.get("notes", "")
        payload = {
            "user_request": user_message,
            "identity": identity,
            "plan_goal": goal,
            "plan_inputs": inputs,
            "shared_notes": notes,
            "context": extra_inputs or {},
        }
        return (
            f"You are the {role.replace('_', ' ')} specialist."
            f"\nTask objective: {goal}"
            f"\nPrimary inputs: {inputs}"
            f"\nShared notes: {notes}"
            f"\nAdditional context:\n{json.dumps(payload, default=str)[:2000]}"
            "\nReturn your result in concise natural language."
        )

    def _resolve_identity(self, config: Optional[Dict[str, Any]]) -> Dict[str, str]:
        base = {
            "user_id": "anonymous",
            "thread_id": "default",
            "org_id": self.config.get("ORG_ID", "default"),
            "security_level": "1",
        }
        if isinstance(config, dict):
            cfg = config.get("configurable") if "configurable" in config else config
            if isinstance(cfg, dict):
                for key in ("user_id", "thread_id", "org_id", "security_level"):
                    if cfg.get(key):
                        base[key] = str(cfg[key])
        return base

    def _memory_summary(self, identity: Dict[str, str]) -> str:
        try:
            combined_filter = {
                "$or": [
                    {"user_id": identity["user_id"]},
                    {"org_id": identity["org_id"]},
                ]
            }
            summary = summarize_memory(combined_filter, org_id=identity["org_id"], max_tokens=8000)
        except Exception as exc:  # pragma: no cover
            logger.debug("Memory summarisation skipped: %s", exc)
            summary = ""
        return summary

    def _inject_runtime_tools(
        self,
        specialist: SpecialistAgent,
        role: str,
        memory_tools: MemoryToolset,
        knowledge_tools: KnowledgeGraphToolset,
    ) -> List[str]:
        functions: Dict[str, Callable[..., Any]] = {}
        signatures: List[Dict[str, Any]] = []

        if role == "data_retrieval":
            def memory_thread_search(query: str, k: int = 5) -> List[str]:
                return memory_tools.search_thread(query, k)

            def memory_user_search(query: str, k: int = 5) -> List[str]:
                return memory_tools.search_user(query, k=k)

            def memory_org_search(query: str, k: int = 5) -> List[str]:
                return memory_tools.search_org(query, k=k)

            def memory_global_search(query: str, k: int = 5) -> List[str]:
                return memory_tools.search_global(query, k)

            def kg_lookup(query: str, k: int = 5) -> List[Dict[str, Any]]:
                return knowledge_tools.search(query, k)

            functions.update(
                {
                    "memory_thread_search": memory_thread_search,
                    "memory_user_search": memory_user_search,
                    "memory_org_search": memory_org_search,
                    "memory_global_search": memory_global_search,
                    "knowledge_graph_search": kg_lookup,
                }
            )
            search_params = {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query."},
                    "k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
            }
            for name, desc in [
                ("memory_thread_search", "Similarity search within short-term thread memory."),
                ("memory_user_search", "Search personalised long-term user memory."),
                ("memory_org_search", "Search organisation-wide knowledge base."),
                ("memory_global_search", "Search global knowledge base."),
                ("knowledge_graph_search", "Search the knowledge graph for relevant facts."),
            ]:
                signatures.append(_tool_signature(name, desc, search_params))

        if role in {"data_processing", "output_generation"}:
            def memory_thread_save(text: str) -> str:
                return memory_tools.save_thread(text)

            def memory_user_save(text: str) -> str:
                return memory_tools.save_user(text)

            functions.update(
                {
                    f"{role}_memory_thread_save": memory_thread_save,
                    f"{role}_memory_user_save": memory_user_save,
                }
            )
            save_params = {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            }
            signatures.extend(
                [
                    _tool_signature(f"{role}_memory_thread_save", "Persist notable insights into thread memory.", save_params),
                    _tool_signature(f"{role}_memory_user_save", "Persist curated findings into user memory.", save_params),
                ]
            )

        if role == "decision_making":
            def kg_upsert(subject: str, predicate: str, obj: str, metadata: Optional[Dict[str, Any]] = None) -> str:
                return knowledge_tools.upsert_fact(subject, predicate, obj, metadata)

            def kg_search(query: str, k: int = 5) -> List[Dict[str, Any]]:
                return knowledge_tools.search(query, k)

            def kg_neighbours(entity: str, depth: int = 2) -> List[Dict[str, Any]]:
                return knowledge_tools.neighbours(entity, depth)

            functions.update(
                {
                    "knowledge_graph_upsert": kg_upsert,
                    "knowledge_graph_search": kg_search,
                    "knowledge_graph_neighbours": kg_neighbours,
                }
            )
            upsert_params = {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "predicate": {"type": "string"},
                    "obj": {"type": "string"},
                    "metadata": {"type": "object"},
                },
                "required": ["subject", "predicate", "obj"],
            }
            search_params = {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
            }
            neighbours_params = {
                "type": "object",
                "properties": {
                    "entity": {"type": "string"},
                    "depth": {"type": "integer", "default": 2, "minimum": 1, "maximum": 5},
                },
                "required": ["entity"],
            }
            signatures.extend(
                [
                    _tool_signature("knowledge_graph_upsert", "Insert or update a fact in the knowledge graph.", upsert_params),
                    _tool_signature("knowledge_graph_search", "Search the knowledge graph for relevant entities.", search_params),
                    _tool_signature("knowledge_graph_neighbours", "Traverse neighbours for an entity in the knowledge graph.", neighbours_params),
                ]
            )

        registered: List[str] = []
        if functions:
            specialist.agent.register_function(functions)
            if specialist.agent.llm_config:
                for sig in signatures:
                    specialist.agent.update_tool_signature(sig, is_remove=None)
            registered = list(functions.keys())
        return registered

    def _clear_runtime_tools(self, specialist: SpecialistAgent, names: List[str]) -> None:
        if not names:
            return
        specialist.agent.register_function({name: None for name in names})
        if specialist.agent.llm_config:
            for name in names:
                try:
                    specialist.agent.update_tool_signature(name, is_remove=True)
                except Exception:  # pragma: no cover - defensive cleanup
                    logger.debug("Failed to remove tool signature for %s", name)


__all__ = ["HierarchicalAutoGenOrchestrator"]
