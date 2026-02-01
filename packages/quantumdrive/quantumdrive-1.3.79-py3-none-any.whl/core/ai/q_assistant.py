"""
---
module: core.ai.q_assistant
summary: Wrapper around agentfoundry Orchestrator with enriched logging.
responsibilities:
  - Initialize Orchestrator with registered tools and LLM
  - Provide a simple API to answer questions
  - Pass identity context (user_id, thread_id, org_id) to Orchestrator for memory scoping
logging:
  levels:
    - INFO: high-level lifecycle and outcomes
    - DEBUG: inputs, constructed configs, timings, sizes
  notes:
    - Exceptions include full tracebacks
    - Question text is truncated to avoid logging sensitive content in full
---

QAssistant: a wrapper around the agentfoundry Orchestrator with rich logging.

This module provides extensive instrumentation to make production diagnosis
easier. It captures initialization details, per-question timings, and the
identity context used to scope Orchestrator memory.
"""

from __future__ import annotations

import logging
import copy
import time
from typing import Optional, Union, Tuple, Any
import os

from agentfoundry.agents.orchestrator import Orchestrator
from langgraph.checkpoint.memory import MemorySaver
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.llm.llm_factory import LLMFactory
from agentfoundry.context.client_state import client_context_scope
from agentfoundry.agents.tools.system_introspection_tool import system_introspection_tool
from agentfoundry.agents.memory.thread_manager import ThreadManager

# Import the new Code Graph tools
from core.code_graph.tool import CodeGraphTool, build_tool
from core.code_graph.builder import CodeGraphBuilder


ALLOWED_TOOL_NAMES = [
    # Memory tools
    "save_thread_memory",
    "search_thread_memory",
    "delete_thread_memory",
    "save_user_memory",
    "search_user_memory",
    "delete_user_memory",
    "save_org_memory",
    "search_org_memory",
    "delete_org_memory",
    "save_global_memory",
    "search_global_memory",
    "summarize_any_memory",
    # User-defined tools
    "user_generated_tool_invoker",
    "user_generated_tool_lister",
    # Document/data helpers
    "document_reader",
    "pandas_explorer",
    "unzip_tool",
    "pdf_creator",
    "summarize_csv",
    # Utilities and integrations
    "geo_location_tool",
    "current_date_time_tool",
    # Scheduling / system
    "system_introspection",
    "schedule_one_time_job",
    "schedule_recurring_job",
    "list_scheduled_jobs",
]

Q_SYSTEM_PROMPT = """You are Q, the intelligent AI companion for the Quantify application.
Your goal is to assist users with understanding and navigating the Quantify platform.
You have access to a 'system_introspection' tool that allows you to inspect the application's configuration, available tools, and documentation.
ALWAYS check your available tools using the ToolRegistry if you are unsure about your capabilities.
If asked about the application version or environment, use 'system_introspection' -> 'app_info' or 'system_context'.
Respond in Markdown: use short headings, bullet/numbered lists, and fenced code blocks for code; avoid raw HTML.
"""


class QAssistant:
    """
    ---
    name: QAssistant
    summary: Thin facade over Orchestrator that adds logging and a convenient API.
    methods:
      - answer_question
      - run_task
    dependencies:
      - agentfoundry.agents.orchestrator.Orchestrator
      - agentfoundry.registry.tool_registry.ToolRegistry
      - agentfoundry.llm.llm_factory.LLMFactory
      - agentfoundry.agents.memory.thread_manager.ThreadManager
    logging:
      info:
        - Initialization progress and success
        - Each question processed and high-level outcome
      debug:
        - Tool registry contents
        - IDs passed to Orchestrator and full config
        - Timings for chat calls
    ---

    A wrapper class for the Orchestrator to provide a simple interface for
    the digital assistant 'Q' to answer questions.
    """

    def __init__(self, user_id: str, org_id: str, orchestrator: Optional[Orchestrator] = None, allowed_tool_names: Optional[list[str]] = None) -> None:
        """Create a new class:`QAssistant` instance.

        The constructor tries to build a class: Orchestrator.  When
        *agentfoundry* is not available (e.g., in lightweight environments or
        during unit-testing), we transparently fall back to a *stub mode* that
        returns an informative placeholder string.  All execution paths are
        thoroughly logged.
        
        Args:
            user_id: The user identity.
            org_id: The organization identity.
            orchestrator: Optional existing Orchestrator instance.
        """

        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        self.org_id = org_id
        self.tool_registry: Optional[ToolRegistry] = None
        self.allowed_tool_names = allowed_tool_names or ALLOWED_TOOL_NAMES

        # Timestamp used to compute initialization duration later.
        _t0 = time.perf_counter()

        # Require agentfoundry components
        self.orchestrator: Orchestrator | None = orchestrator
        
        if ToolRegistry is None or LLMFactory is None or Orchestrator is None:
            self.logger.error("Agentfoundry dependencies missing; cannot initialize Orchestrator")
            raise RuntimeError("Agentfoundry unavailable: ToolRegistry/LLMFactory/Orchestrator missing")

        # -------------------------------------------------------------------
        # Real agent initialisation
        # -------------------------------------------------------------------
        if not self.orchestrator:
            try:
                # Resolve LLM provider/model via AgentFoundry config + env overrides.
                # Environment variables can be populated via Secrets Manager at startup.
                self.logger.debug("Creating LLM instances using factory/provider defaults")
                llm = LLMFactory.get_llm_by_role(role="reasoning")
                formatter_llm = LLMFactory.get_llm_by_role(role="formatting")

                self.tool_registry = ToolRegistry()
                self.tool_registry.load_tools_from_directory()
                self.tool_registry.register_tool(system_introspection_tool)

                # Register the new Code Graph tools
                code_graph_tool_instance = CodeGraphTool()
                self.tool_registry.register_tool(code_graph_tool_instance.as_tool())
                self.tool_registry.register_tool(build_tool)
                
                self.logger.info(f"Registered tools: {self.tool_registry.list_tools()}")

                # Ensure the orchestrator has an agent→tools map. If none is provided,
                # default to a single general agent with all registered tools.
                available_tools = self.tool_registry.as_langchain_tools()
                self.logger.info(f"QAssistant available tools: {[tool.name for tool in available_tools]}")
                allowed_names = set(self.allowed_tool_names)
                self.logger.info(f"QAssistant allowed tools: {allowed_names}")
                selected_tools = [t for t in available_tools if getattr(t, "name", "") in allowed_names]

                if not selected_tools:
                    missing = sorted(self.allowed_tool_names)
                    msg = (
                        "No tools matched the allowed list; aborting QAssistant init to avoid exposing all tools. "
                        f"Allowed list: {missing}"
                    )
                    self.logger.error(msg)
                    raise RuntimeError(msg)

                missing = allowed_names.difference({getattr(t, 'name', '') for t in selected_tools})
                if missing:
                    self.logger.warning(
                        "Some allowed tools were not found in registry and will be skipped: %s",
                        sorted(missing),
                    )
                self.logger.info("Filtered tools to %d allowed entries.", len(selected_tools))
                self.tool_registry.agent_tools = {"general_agent": selected_tools}
                self.logger.info("Configured agent_tools mapping with %d tools.", len(selected_tools))

                # Initialize the Orchestrator; failure is fatal
                self.orchestrator = Orchestrator(self.tool_registry, llm=llm, formatter_llm=formatter_llm, base_prompt=Q_SYSTEM_PROMPT)
                self.logger.info("Orchestrator initialized successfully.")

                # NOTE: Code graph build is disabled here to avoid blocking request-time init.
                # It should be moved to a global background task at process startup.
                # self.logger.info("Building initial code graph...")
                # try:
                #     builder = CodeGraphBuilder(project_root=os.getcwd())
                #     builder.build_graph()
                #     self.logger.info("Initial code graph built successfully.")
                # except Exception as build_ex:
                #     self.logger.error(f"Failed to build initial code graph: {build_ex}")

            except Exception as e:  # pragma: no cover
                self.logger.exception(f"Failed to initialise Orchestrator: {e}")
                raise
        
        # --- NEW LOGIC START ---
        self.thread_manager = ThreadManager()
        
        # 1. Try to find the last active thread for this user/org
        latest_thread = self.thread_manager.get_latest_thread(user_id, org_id)
        
        if latest_thread:
            # Resume the existing conversation
            self.thread_id = latest_thread
            self.logger.info(f"Resuming existing thread: {self.thread_id}")
        else:
            # First time user? Start at "1" (or whatever your default is)
            self.thread_id = self.thread_manager.generate_next_thread_id(user_id, org_id)
            self.logger.info(f"Starting new thread: {self.thread_id}")
        # --- NEW LOGIC END ---

        self.memory = MemorySaver() # KEY CHANGE: QAssistant owns the session state now
        
        self.config = {
            "configurable": {
                "user_id": user_id,
                "thread_id": self.thread_id,
                "org_id": org_id
            }
        }

    def answer_question(
            self,
            question: str,
            client_context: Optional[dict] = None,
            user_assertion: Optional[str] = None,
    ) -> str:
        """
        ---
        method: answer_question
        summary: Answer a user question using Orchestrator with memory scoped by IDs.
        parameters:
          question:
            type: str
            required: true
            description: The user's natural-language question.
        returns:
          type: str
          description: Assistant's reply.
        raises:
          - RuntimeError: if the underlying agent is not initialized.
          - Exception: any error raised by the Orchestrator; logged with traceback.
        logging:
          info:
            - Start/end of processing with truncated question and reply
          debug:
            - IDs used and constructed config
            - Call duration and reply length
        ---

        Answer a question using the underlying Orchestrator agent. The
        Orchestrator maintains memory keyed by the provided IDs.
        """

        self.logger.info(f"Processing question: {question[:85]} from user_id={self.user_id} thread_id={self.thread_id} org_id={self.org_id}...")

        if not self.orchestrator:
            self.logger.error("QAssistant agent not initialized; aborting")
            raise RuntimeError("QAssistant unavailable: Orchestrator not initialized")

        _t0 = time.perf_counter()
        try:
            self.logger.info("QAssistant mode=agent (chat)")
            messages = []
            # Opportunistic user-memory recall targeted to the question to
            # improve personal answers (e.g., "my eye color") even when the
            # agent chooses not to invoke tools on its own.
            try:
                if self.user_id and self.org_id:
                    from agentfoundry.agents.memory.user_memory import UserMemory as _UM
                    um = _UM(self.user_id, self.org_id)
                    hits = um.semantic_search(question, caller_role_level=0, k=5)
                    if hits:
                        snippet = "\n".join(f"- {h}" for h in hits)
                        self.logger.info("QAssistant preloaded %d user-memory hits for query", len(hits))
                        messages.append({"role": "system", "content": f"USER_MEMORY_HITS:\n{snippet}"})
            except Exception as _um_ex:  # noqa: E722  (defensive)
                self.logger.debug("UserMemory preload failed: %s", _um_ex)

            messages.append({"role": "user", "content": question})
            
            self.logger.debug(
                "Calling orchestrator.process_request with ids user_id=%s thread_id=%s org_id=%s",
                self.config["configurable"]["user_id"], self.config["configurable"]["thread_id"], self.config["configurable"]["org_id"],
            )
            effective_config = copy.deepcopy(self.config)
            if user_assertion:
                effective_config["configurable"]["entra_user_assertion"] = user_assertion
                self.logger.debug("Added entra_user_assertion to config for this request.")
            with client_context_scope(client_context or {}):
                # Older Orchestrator expects positional message; avoid keyword mismatch
                response = self.orchestrator.process_request(messages, checkpointer=self.memory, config=effective_config)
            elapsed = time.perf_counter() - _t0
            self.logger.debug("agent.process_request completed in %.3f s (reply_len=%d)", elapsed, len(str(response)))
            self.logger.info("Response: %s", response)
            return response
        except Exception:
            self.logger.exception("Exception while processing question: %s", question)
            raise

    def run_task(self, task: str, *, use_memory: bool = False, additional: bool = False,
                 allow_tools: bool = False, allowed_tool_names: list[str] | None = None,
                 file_ids: list | None = None, vector_store_id: str | None = None,
                 model_role: str = "reasoning") -> Union[str, Tuple[str, Any]]:
        """
        ---
        method: run_task
        summary: Execute a single-turn task via Orchestrator.run_task.
        notes:
          - Stateless helper intended for one-off operations or smoke tests.
          - Set use_memory=true to inject summarized memory context (optional).
        parameters:
          task:
            type: str
            required: true
            description: The instruction or question to execute.
          use_memory:
            type: bool
            required: false
            default: false
            description: When true, Orchestrator adds a summarized memory context.
          additional:
            type: bool
            required: false
            default: false
            description: When true, also returns full supervisor outputs.
        returns:
          type: str | tuple[str, Any]
          description: Assistant reply, optionally with the full responses' payload.
        raises:
          - RuntimeError: if the agent is not initialized.
          - Exception: bubbled up from the Orchestrator and logged with traceback.
        ---

        Execute a single-turn task through the Orchestrator's run_task helper.
        """
        self.logger.info(f"Running task (stateless): {task[:85]}...")
        try:
            _n_files = len(file_ids or [])
        except Exception:
            _n_files = 0
        self.logger.debug(
            "run_task params: use_memory=%s additional=%s allow_tools=%s allowed_tool_names=%s file_ids_count=%d vector_store_id=%s",
            use_memory, additional, allow_tools, bool(allowed_tool_names), _n_files, bool(vector_store_id),
        )

        if not self.orchestrator:
            self.logger.error("QAssistant agent not initialized; aborting")
            raise RuntimeError("QAssistant unavailable: Orchestrator not initialized")

        _t0 = time.perf_counter()
        try:
            # If file IDs are provided, route via chat() so the underlying
            # Orchestrator can attach files to the request (Responses API).
            if file_ids:
                self.logger.info(
                    "Routing run_task via chat() due to file attachments (files=%d)",
                    len(file_ids or []),
                )
                messages = [{"role": "user", "content": task}]
                # Use the same config path; Orchestrator.chat will include memory
                # as a system message automatically.
                result = self.orchestrator.chat(messages=messages, checkpointer=self.memory, config=self.config, additional=additional, file_ids=file_ids, vector_store_id=vector_store_id)
            else:
                self.logger.debug(
                    f"Calling orchestrator.run_task(use_memory={use_memory}, additional={additional}) without file attachments"
                )
                result = self.orchestrator.run_task(
                    task,
                    checkpointer=self.memory,
                    use_memory=use_memory,
                    additional=additional,
                    allow_tools=allow_tools,
                    allowed_tool_names=allowed_tool_names,
                    config=self.config,
                    model_role=model_role,
                )
            elapsed = time.perf_counter() - _t0
            # Normalize logging for both return shapes
            if isinstance(result, tuple) and len(result) >= 1:
                reply = result[0]
            else:
                reply = result  # type: ignore[assignment]
            self.logger.debug(
                "run_task completed in %.3f s (reply_len=%d, routed_via=%s)",
                elapsed,
                len(str(reply)),
                ("chat" if file_ids else "run_task"),
            )
            self.logger.info("Task response head: %s", str(reply)[:300])
            return result
        except Exception:
            self.logger.exception("Exception while running task: %s", task)
            raise


if __name__ == "__main__":
    # Initialize required components
    # Create a QAssistant instance
    assistant = QAssistant(user_id="123", org_id="test_org")

    # Test with a simple question
    question = "Who wrote the book 'Core Security Patterns'?"
    response = assistant.answer_question(question)

    # Verify response
    print(f"Response: {response}")
