"""
DynamicAgentRuntime - An agent that loads its configuration from the database.

This allows agents to be defined and modified via the AgentDefinition model
without requiring code changes.

Supports:
- RAG (Retrieval Augmented Generation) for knowledge sources with inclusion_mode='rag'
- Conversation-scoped memory via the 'remember' tool
"""

import json
import logging
from typing import Any, Optional
from uuid import UUID

from agent_runtime_core.registry import AgentRuntime
from agent_runtime_core.interfaces import RunContext, RunResult, EventType
from agent_runtime_core.agentic_loop import run_agentic_loop
from django_agent_runtime.runtime.llm import get_llm_client_for_model, DEFAULT_MODEL
from django_agent_runtime.models import AgentDefinition
from django_agent_runtime.dynamic_tools.executor import DynamicToolExecutor

logger = logging.getLogger(__name__)


# =============================================================================
# Memory Tool Definitions
# =============================================================================

# Conversation-scoped memory (ephemeral, lost when conversation ends)
MEMORY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "remember",
        "description": (
            "Store information to remember. Use this to remember important facts about "
            "the user, their preferences, project details, or anything useful to recall. "
            "Use semantic dot-notation keys like 'user.name', 'user.preferences.theme', "
            "'project.goal'. By default, memories persist across conversations for this user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": (
                        "A semantic key using dot-notation for what you're remembering "
                        "(e.g., 'user.name', 'user.preferences.language', 'project.goal')"
                    ),
                },
                "value": {
                    "type": "string",
                    "description": "The information to remember",
                },
                "scope": {
                    "type": "string",
                    "enum": ["conversation", "user", "system"],
                    "description": (
                        "Memory scope: 'conversation' (this chat only), "
                        "'user' (persists across chats, default), "
                        "'system' (shared with other agents)"
                    ),
                },
            },
            "required": ["key", "value"],
        },
    },
}

# Tool to recall memories
RECALL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recall",
        "description": (
            "Recall stored memories. Use this to retrieve information you've previously "
            "remembered about the user or project. You can recall a specific key or list "
            "all memories matching a prefix."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": (
                        "The specific key to recall (e.g., 'user.name') or a prefix "
                        "to list all matching memories (e.g., 'user.preferences')"
                    ),
                },
                "scope": {
                    "type": "string",
                    "enum": ["conversation", "user", "system", "all"],
                    "description": (
                        "Which scope to search: 'conversation', 'user', 'system', "
                        "or 'all' (default) to search all scopes"
                    ),
                },
            },
            "required": ["key"],
        },
    },
}

# Tool to forget memories
FORGET_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "forget",
        "description": (
            "Forget/delete a stored memory. Use this when the user asks you to forget "
            "something or when information is no longer relevant."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key of the memory to forget (e.g., 'user.name')",
                },
                "scope": {
                    "type": "string",
                    "enum": ["conversation", "user", "system"],
                    "description": "The scope of the memory to forget",
                },
            },
            "required": ["key"],
        },
    },
}


class DynamicAgentRuntime(AgentRuntime):
    """
    An agent runtime that loads its configuration from an AgentDefinition.
    
    This allows agents to be created and modified via the database/API
    without requiring code changes or deployments.
    """
    
    def __init__(self, agent_definition: AgentDefinition):
        self._definition = agent_definition
        self._config: Optional[dict] = None
    
    @property
    def key(self) -> str:
        """Return the agent's slug as its key."""
        return self._definition.slug
    
    @property
    def config(self) -> dict:
        """Get the effective configuration (cached). Use get_config_async() in async contexts."""
        if self._config is None:
            self._config = self._definition.get_effective_config()
        return self._config

    async def get_config_async(self) -> dict:
        """Get the effective configuration in an async-safe way."""
        from asgiref.sync import sync_to_async
        if self._config is None:
            self._config = await sync_to_async(self._definition.get_effective_config)()
        return self._config

    def refresh_config(self):
        """Refresh the configuration from the database."""
        self._definition.refresh_from_db()
        self._config = None

    async def run(self, ctx: RunContext) -> RunResult:
        """Execute the agent with the dynamic configuration and agentic loop."""
        config = await self.get_config_async()

        # Check if memory is enabled (default: True)
        extra_config = config.get("extra", {})
        memory_enabled = extra_config.get("memory_enabled", True)

        # Build the messages list
        messages = []

        # Start with system-level shared knowledge (if agent is part of a system)
        system_context = await self._get_system_context()
        system_prefix = ""
        if system_context:
            system_prefix = system_context.get_system_prompt_prefix()
            logger.debug(f"Injecting system context from '{system_context.system_name}'")

        # Add agent's system prompt
        agent_prompt = config.get("system_prompt", "")

        # Combine system prefix with agent prompt
        if system_prefix and agent_prompt:
            system_prompt = f"{system_prefix}\n\n---\n\n{agent_prompt}"
        elif system_prefix:
            system_prompt = system_prefix
        else:
            system_prompt = agent_prompt

        # Add knowledge that should always be included
        knowledge_context = self._build_knowledge_context(config)
        if knowledge_context:
            system_prompt = f"{system_prompt}\n\n{knowledge_context}"

        # Add RAG-retrieved knowledge based on user's query
        rag_context = await self._retrieve_rag_knowledge(config, ctx)
        if rag_context:
            system_prompt = f"{system_prompt}\n\n{rag_context}"

        # Add conversation memories (if memory is enabled and we have context)
        memory_store = None
        if memory_enabled:
            memory_store = await self._get_memory_store(ctx)
            if memory_store:
                memory_context = await self._recall_memories(memory_store, ctx)
                if memory_context:
                    system_prompt = f"{system_prompt}\n\n{memory_context}"

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        messages.extend(ctx.input_messages)

        # Build tool schemas - include memory tools if memory is enabled
        tools = self._build_tool_schemas(config)
        if memory_enabled:
            tools.append(MEMORY_TOOL_SCHEMA)
            tools.append(RECALL_TOOL_SCHEMA)
            tools.append(FORGET_TOOL_SCHEMA)

        tool_map = self._build_tool_map(config)  # Maps tool name to execution info

        # Get model: params override > agent config > default
        model = ctx.params.get("model") or config.get("model") or DEFAULT_MODEL
        model_settings = config.get("model_settings", {})

        # Get LLM client for the model (auto-detects provider)
        llm = get_llm_client_for_model(model)

        # Initialize tool executor for dynamic tools
        tool_executor = DynamicToolExecutor()

        # Create tool executor function for the agentic loop
        async def execute_tool(tool_name: str, tool_args: dict) -> str:
            # Handle the built-in memory tools
            if tool_name == "remember":
                return await self._execute_remember_tool(tool_args, memory_store, ctx)
            if tool_name == "recall":
                return await self._execute_recall_tool(tool_args, memory_store, ctx)
            if tool_name == "forget":
                return await self._execute_forget_tool(tool_args, memory_store, ctx)

            return await self._execute_tool(
                tool_name, tool_args, tool_map, tool_executor, ctx
            )

        try:
            # Use the shared agentic loop
            result = await run_agentic_loop(
                llm=llm,
                messages=messages,
                tools=tools if tools else None,
                execute_tool=execute_tool,
                ctx=ctx,
                model=model,
                max_iterations=15,
                **model_settings,
            )

            # Note: run_agentic_loop already emits ASSISTANT_MESSAGE events,
            # so we don't emit here to avoid duplicate messages in the UI.

            return RunResult(
                final_output={"response": result.final_content},
                final_messages=result.messages,
            )

        except Exception as e:
            logger.exception(f"Error in DynamicAgentRuntime for {self.key}")
            await ctx.emit(EventType.RUN_FAILED, {"error": str(e)})
            raise

    async def _get_system_context(self):
        """
        Get the SystemContext if this agent is part of an AgentSystem.

        Returns:
            SystemContext with shared knowledge, or None if agent is not in a system
        """
        from asgiref.sync import sync_to_async
        from django_agent_runtime.models import AgentSystemMember

        try:
            # Check if this agent is a member of any system
            membership = await sync_to_async(
                lambda: AgentSystemMember.objects.filter(
                    agent=self._definition
                ).select_related('system').first()
            )()

            if membership and membership.system:
                # Get the SystemContext from the system
                system_context = await sync_to_async(
                    membership.system.get_system_context
                )()
                return system_context

        except Exception as e:
            logger.warning(f"Failed to get system context: {e}")

        return None

    async def _get_memory_store(self, ctx: RunContext) -> Optional["DjangoSharedMemoryStore"]:
        """
        Get the shared memory store for this user, if available.

        Returns None if we don't have the required context (authenticated user).
        Privacy enforcement: Only authenticated users can have persistent memories.
        """
        from django_agent_runtime.persistence.stores import DjangoSharedMemoryStore

        # Need authenticated user for memory (privacy enforcement)
        user_id = ctx.metadata.get("user_id")

        if not user_id:
            logger.debug("Memory not available: no authenticated user")
            return None

        try:
            # Get the user object
            from django.contrib.auth import get_user_model
            from asgiref.sync import sync_to_async

            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=user_id)

            return DjangoSharedMemoryStore(user=user)
        except Exception as e:
            logger.warning(f"Failed to create memory store: {e}")
            return None

    async def _recall_memories(
        self,
        memory_store: "DjangoSharedMemoryStore",
        ctx: RunContext,
    ) -> str:
        """
        Recall all memories for this user and format for the prompt.
        Includes user-scoped and system-scoped memories.
        """
        try:
            # Get user-scoped memories
            user_memories = await memory_store.list(scope="user", limit=50)

            # Get system-scoped memories (shared across agents)
            system_memories = await memory_store.list(scope="system", limit=50)

            # Get conversation-scoped memories
            conversation_memories = []
            if ctx.conversation_id:
                conversation_memories = await memory_store.list(
                    scope="conversation",
                    conversation_id=ctx.conversation_id,
                    limit=50,
                )

            all_memories = user_memories + system_memories + conversation_memories

            if all_memories:
                logger.info(f"Recalled {len(all_memories)} memories for user")
                return self._format_memories_for_prompt(all_memories)
        except Exception as e:
            logger.warning(f"Failed to recall memories: {e}")
        return ""

    def _format_memories_for_prompt(self, memories: list) -> str:
        """Format memories for inclusion in a system prompt."""
        if not memories:
            return ""

        lines = ["# Remembered Information", ""]

        # Group by scope
        by_scope = {"user": [], "system": [], "conversation": []}
        for mem in memories:
            scope = mem.scope if hasattr(mem, 'scope') else "user"
            if scope in by_scope:
                by_scope[scope].append(mem)

        if by_scope["user"]:
            lines.append("## About This User")
            for mem in by_scope["user"]:
                display_key = mem.key.replace(".", " > ").replace("_", " ").title()
                lines.append(f"- **{display_key}**: {mem.value}")
            lines.append("")

        if by_scope["system"]:
            lines.append("## Shared Knowledge")
            for mem in by_scope["system"]:
                display_key = mem.key.replace(".", " > ").replace("_", " ").title()
                lines.append(f"- **{display_key}**: {mem.value}")
            lines.append("")

        if by_scope["conversation"]:
            lines.append("## This Conversation")
            for mem in by_scope["conversation"]:
                display_key = mem.key.replace(".", " > ").replace("_", " ").title()
                lines.append(f"- **{display_key}**: {mem.value}")
            lines.append("")

        return "\n".join(lines)

    async def _execute_remember_tool(
        self,
        args: dict,
        memory_store: Optional["DjangoSharedMemoryStore"],
        ctx: RunContext,
    ) -> str:
        """Execute the remember tool to store a memory."""
        if not memory_store:
            return json.dumps({
                "error": "Memory not available",
                "hint": "Memory requires a logged-in user",
            })

        key = args.get("key", "").strip()
        value = args.get("value", "").strip()
        scope = args.get("scope", "user").strip()

        if not key:
            return json.dumps({"error": "Missing required parameter: key"})
        if not value:
            return json.dumps({"error": "Missing required parameter: value"})
        if scope not in ("conversation", "user", "system"):
            return json.dumps({"error": f"Invalid scope: {scope}"})

        try:
            # For conversation scope, need conversation_id
            conversation_id = ctx.conversation_id if scope == "conversation" else None

            await memory_store.set(
                key=key,
                value=value,
                scope=scope,
                source=f"agent:{self.key}",
                conversation_id=conversation_id,
            )
            logger.info(f"Stored memory: {key} (scope={scope})")
            return json.dumps({
                "success": True,
                "message": f"Remembered: {key} (scope: {scope})",
            })
        except Exception as e:
            logger.exception(f"Failed to store memory: {key}")
            return json.dumps({"error": str(e)})

    async def _execute_recall_tool(
        self,
        args: dict,
        memory_store: Optional["DjangoSharedMemoryStore"],
        ctx: RunContext,
    ) -> str:
        """Execute the recall tool to retrieve memories."""
        if not memory_store:
            return json.dumps({
                "error": "Memory not available",
                "hint": "Memory requires a logged-in user",
            })

        key = args.get("key", "").strip()
        scope = args.get("scope", "all").strip()

        if not key:
            return json.dumps({"error": "Missing required parameter: key"})

        try:
            results = []

            # Determine which scopes to search
            scopes_to_search = []
            if scope == "all":
                scopes_to_search = ["user", "system", "conversation"]
            else:
                scopes_to_search = [scope]

            for s in scopes_to_search:
                conversation_id = ctx.conversation_id if s == "conversation" else None

                # Try exact match first
                item = await memory_store.get(key, scope=s, conversation_id=conversation_id)
                if item:
                    results.append({
                        "key": item.key,
                        "value": item.value,
                        "scope": item.scope,
                        "source": item.source,
                    })
                else:
                    # Try prefix match
                    items = await memory_store.list(
                        prefix=key,
                        scope=s,
                        conversation_id=conversation_id,
                        limit=20,
                    )
                    for item in items:
                        results.append({
                            "key": item.key,
                            "value": item.value,
                            "scope": item.scope,
                            "source": item.source,
                        })

            if results:
                return json.dumps({"memories": results})
            else:
                return json.dumps({"memories": [], "message": f"No memories found for key: {key}"})

        except Exception as e:
            logger.exception(f"Failed to recall memory: {key}")
            return json.dumps({"error": str(e)})

    async def _execute_forget_tool(
        self,
        args: dict,
        memory_store: Optional["DjangoSharedMemoryStore"],
        ctx: RunContext,
    ) -> str:
        """Execute the forget tool to delete a memory."""
        if not memory_store:
            return json.dumps({
                "error": "Memory not available",
                "hint": "Memory requires a logged-in user",
            })

        key = args.get("key", "").strip()
        scope = args.get("scope", "user").strip()

        if not key:
            return json.dumps({"error": "Missing required parameter: key"})
        if scope not in ("conversation", "user", "system"):
            return json.dumps({"error": f"Invalid scope: {scope}"})

        try:
            conversation_id = ctx.conversation_id if scope == "conversation" else None

            deleted = await memory_store.delete(
                key=key,
                scope=scope,
                conversation_id=conversation_id,
            )

            if deleted:
                logger.info(f"Deleted memory: {key} (scope={scope})")
                return json.dumps({
                    "success": True,
                    "message": f"Forgot: {key}",
                })
            else:
                return json.dumps({
                    "success": False,
                    "message": f"No memory found with key: {key}",
                })

        except Exception as e:
            logger.exception(f"Failed to forget memory: {key}")
            return json.dumps({"error": str(e)})
    
    def _build_knowledge_context(self, config: dict) -> str:
        """Build context string from always-included knowledge sources."""
        parts = []
        for knowledge in config.get("knowledge", []):
            if knowledge.get("inclusion_mode") == "always":
                content = knowledge.get("content")
                if content:
                    name = knowledge.get("name", "Knowledge")
                    parts.append(f"## {name}\n{content}")
        return "\n\n".join(parts)

    async def _retrieve_rag_knowledge(self, config: dict, ctx: RunContext) -> str:
        """
        Retrieve relevant knowledge using RAG for knowledge sources with inclusion_mode='rag'.

        Args:
            config: The agent's effective configuration
            ctx: The run context containing user messages

        Returns:
            Formatted string of retrieved knowledge, or empty string if no RAG knowledge
        """
        # Check if there are any RAG knowledge sources
        rag_knowledge = [
            k for k in config.get("knowledge", [])
            if k.get("inclusion_mode") == "rag" and k.get("rag", {}).get("status") == "indexed"
        ]

        if not rag_knowledge:
            return ""

        # Get the user's query from the last user message
        user_query = ""
        for msg in reversed(ctx.input_messages):
            if msg.get("role") == "user":
                user_query = msg.get("content", "")
                break

        if not user_query:
            return ""

        try:
            from django_agent_runtime.rag import KnowledgeRetriever

            retriever = KnowledgeRetriever()
            rag_config = config.get("rag_config", {})

            # Retrieve relevant knowledge
            context = await retriever.retrieve_for_agent(
                agent_id=str(self._definition.id),
                query=user_query,
                rag_config=rag_config,
            )

            return context

        except Exception as e:
            logger.warning(f"Error retrieving RAG knowledge: {e}")
            return ""
    
    def _build_tool_schemas(self, config: dict) -> list:
        """Build OpenAI-format tool schemas from config."""
        schemas = []
        for tool in config.get("tools", []):
            # Skip the _meta field when building schema
            schema = {
                "type": tool.get("type", "function"),
                "function": tool.get("function", {}),
            }
            schemas.append(schema)
        return schemas

    def _build_tool_map(self, config: dict) -> dict:
        """Build a map of tool name to execution info."""
        tool_map = {}
        for tool in config.get("tools", []):
            func_info = tool.get("function", {})
            tool_name = func_info.get("name")
            if tool_name:
                # Get execution metadata from _meta field
                meta = tool.get("_meta", {})
                tool_map[tool_name] = {
                    "function_path": meta.get("function_path"),
                    "tool_id": meta.get("tool_id"),
                    "is_dynamic": meta.get("is_dynamic", False),
                }
        return tool_map

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: dict,
        tool_map: dict,
        executor: "DynamicToolExecutor",
        ctx: RunContext,
    ) -> str:
        """Execute a tool and return its result."""
        tool_info = tool_map.get(tool_name, {})
        function_path = tool_info.get("function_path")

        if not function_path:
            return json.dumps({"error": f"Tool '{tool_name}' has no function_path configured"})

        try:
            # Get user_id from context metadata if available
            user_id = ctx.metadata.get("user_id")

            # Execute the tool
            result = await executor.execute(
                function_path=function_path,
                arguments=tool_args,
                agent_run_id=ctx.run_id,
                user_id=user_id,
                tool_id=tool_info.get("tool_id"),
            )

            # Convert result to string if needed
            if isinstance(result, str):
                return result
            return json.dumps(result)

        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            return json.dumps({"error": str(e)})

