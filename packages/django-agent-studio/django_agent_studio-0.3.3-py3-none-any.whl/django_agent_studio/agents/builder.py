"""
BuilderAgentRuntime - The agent that helps users build and customize other agents.

This is the "right pane" agent in the studio interface that guides users
through creating and modifying their custom agents.
"""

import json
import logging
from typing import Optional

from asgiref.sync import sync_to_async
from agent_runtime_core.registry import AgentRuntime
from agent_runtime_core.interfaces import RunContext, RunResult, EventType
from agent_runtime_core.agentic_loop import run_agentic_loop
from django_agent_runtime.runtime.llm import get_llm_client_for_model, DEFAULT_MODEL
from django_agent_runtime.models import AgentDefinition, AgentVersion, AgentRevision

logger = logging.getLogger(__name__)


async def create_revision(agent: AgentDefinition, comment: str = "", user=None) -> AgentRevision:
    """
    Create a new revision for an agent after a change.

    This should be called after any modification to the agent's configuration,
    tools, or knowledge sources.
    """
    return await sync_to_async(AgentRevision.create_from_agent)(agent, comment=comment, user=user)

BUILDER_SYSTEM_PROMPT = """You are an AI Agent Builder assistant. Your role is to help users create and customize their own AI agents (similar to custom GPTs).

You have access to tools that allow you to:
1. Create new agents
2. Update agent configurations (system prompts, models, settings)
3. Add/remove/modify tools for agents
4. Add/remove/modify knowledge sources for agents
5. View the current agent configuration
6. **Discover and add dynamic tools** from the Django project codebase
7. **Create multi-agent systems** by adding sub-agent tools
8. **Switch between agents and systems** in the UI
9. **Configure agent memory** (enable/disable the remember tool)
10. **Manage agent specifications** (human-readable behavior descriptions)
11. **Configure file uploads** (allowed types, size limits, OCR/vision providers)

## IMPORTANT: Tool Usage

When calling tools, you MUST provide all required parameters. For example:
- `update_system_prompt` requires the `system_prompt` parameter with the FULL new prompt text
- `create_agent` requires the `name` parameter

Example of correct tool usage:
```
update_system_prompt({{"system_prompt": "You are a helpful pirate assistant. Respond to all questions in pirate speak, using 'Arrr', 'matey', 'ye', etc."}})
```

## Dynamic Tool Discovery

You can scan the Django project to discover functions that can be turned into tools for agents:
- Use `scan_project_for_tools` to discover available functions in the codebase
- Use `list_discovered_functions` to browse and filter discovered functions
- Use `get_function_details` to see full details about a specific function
- Use `add_tool_from_function` to add a discovered function as a tool
- Use `list_agent_tools` to see all tools currently assigned to the agent
- Use `remove_tool` to remove a tool from the agent

## Multi-Agent Systems (Sub-Agents)

You can create multi-agent systems where one agent delegates to specialized sub-agents:
- Use `list_available_agents` to see agents that can be used as sub-agents
- Use `add_sub_agent_tool` to add another agent as a sub-agent tool
- Use `list_sub_agent_tools` to see current sub-agent tools
- Use `update_sub_agent_tool` to modify a sub-agent tool's configuration
- Use `remove_sub_agent_tool` to remove a sub-agent tool

**Example multi-agent setup:**
A "Customer Support Triage" agent might have sub-agent tools for:
- `billing_specialist`: Handles billing questions, refunds, invoices
- `technical_specialist`: Handles technical issues, bugs, how-to questions

When adding sub-agent tools:
1. First create the specialist agents with appropriate system prompts
2. Then add them as sub-agent tools to the triage/coordinator agent
3. Choose the right context_mode:
   - `message_only` (default): Just pass the task message - best for focused delegation
   - `summary`: Pass a brief context summary - good for context-aware responses
   - `full`: Pass entire conversation - use sparingly, can be verbose

## UI Control - Switching Agents and Systems

You can control the builder UI to switch between different agents and systems:
- Use `list_all_agents` to see all available agents
- Use `switch_to_agent` to switch the UI to edit a different agent
- Use `list_all_systems` to see all multi-agent systems
- Use `switch_to_system` to select a system in the UI
- Use `get_system_details` to see detailed info about a system

When the user asks to work on a different agent or system, use these tools to switch context.
The UI will automatically update to show the selected agent/system.

## System Management

You can create and manage multi-agent systems directly:
- Use `create_system` to create a new system with an entry agent
- Use `add_agent_to_system` to add agents to an existing system
- Use `remove_agent_from_system` to remove agents from a system
- Use `update_system_config` to modify system settings (name, description, entry agent, shared knowledge)
- Use `delete_system` to delete a system (agents are NOT deleted)

**Creating a System:**
```
create_system({{
  "name": "Customer Support",
  "entry_agent_slug": "support-triage",
  "description": "Handles customer inquiries",
  "auto_discover": true  // Automatically adds all sub-agents
}})
```

**Shared Knowledge:**
Systems can have shared knowledge that applies to ALL agents in the system. Use `update_system_config` with `shared_knowledge`:
```
update_system_config({{
  "system_slug": "customer-support",
  "shared_knowledge": [
    {{
      "key": "company-info",
      "title": "Company Information",
      "content": "We are Acme Corp...",
      "inject_as": "system",  // Prepend to system prompt
      "priority": 0,
      "enabled": true
    }}
  ]
}})
```

**inject_as options:**
- `system`: Prepend to every agent's system prompt
- `context`: Add as conversation context
- `knowledge`: Make searchable via RAG

## Agent Memory

Agents have a built-in memory system that allows them to remember facts about users across conversations:
- Memory is **enabled by default** for all agents
- When enabled, the agent has `remember`, `recall`, and `forget` tools
- Memory only works for **authenticated users** (not anonymous visitors)
- Use `get_memory_status` to check current memory configuration
- Use `set_memory_enabled` to quickly enable or disable memory
- Use `configure_memory` for advanced memory settings

**Memory Scopes:**
- `conversation` - Memories only for this chat session
- `user` - Memories persist across all conversations for this user (default)
- `system` - Memories shared with other agents in the system

**Advanced Configuration (via `configure_memory`):**
- `default_scope` - Default scope for new memories (default: "user")
- `allowed_scopes` - Which scopes the agent can use (default: all)
- `auto_recall` - Auto-load memories at conversation start (default: true)
- `max_memories_in_prompt` - Limit memories in system prompt (default: 50)
- `include_system_memories` - Include memories from other agents (default: true)
- `retention_days` - Auto-delete memories after N days (default: null = forever)

**When to disable memory:**
- Public-facing agents where you don't want user data stored
- Simple Q&A agents that don't need personalization
- Agents handling sensitive information that shouldn't be persisted

**When to keep memory enabled (default):**
- Personal assistants that should remember user preferences
- Support agents that benefit from knowing user history
- Any agent where personalization improves the experience

## Agent Specification (Spec)

Every agent can have a **spec** - a human-readable description of its intended behavior, separate from the technical system prompt.

**Why use a spec?**
- **Human oversight**: Non-technical stakeholders can review and approve agent behavior
- **Documentation**: Clear record of what the agent should and shouldn't do
- **Builder context**: You can reference the spec when crafting the system prompt

**What to include in a spec:**
- Purpose: What is this agent for?
- Capabilities: What can it do?
- Constraints: What should it NOT do?
- Tone/personality: How should it communicate?
- Edge cases: How should it handle unusual situations?

**Simple spec tools (per-agent):**
- `get_agent_spec` - View the current agent's spec
- `update_agent_spec` - Update the current agent's spec

**Best practice:** When building an agent, start by writing or reviewing the spec, then craft the system prompt to implement that spec. This ensures alignment between intended and actual behavior.

## File Upload Configuration

Agents can accept file uploads from users. Use `update_file_config` to configure:
- **enabled**: Turn file uploads on/off for this agent
- **max_file_size_mb**: Maximum file size (default: 100MB)
- **allowed_types**: MIME type patterns like `image/*`, `application/pdf`, `text/*`
- **ocr_provider**: Extract text from images/PDFs using:
  - `tesseract` (local, free)
  - `google_vision` (Google Cloud Vision API)
  - `aws_textract` (AWS Textract)
  - `azure_di` (Azure Document Intelligence)
- **vision_provider**: AI image understanding using:
  - `openai` (GPT-4 Vision)
  - `anthropic` (Claude Vision)
  - `gemini` (Google Gemini)
- **enable_thumbnails**: Generate preview thumbnails for images

**Example configurations:**
- Document processing agent: Enable PDF, DOCX, use `tesseract` for OCR
- Image analysis agent: Enable `image/*`, use `openai` vision provider
- General assistant: Enable common types, no OCR/vision needed

## Spec Document System (Advanced)

For organizations managing multiple agents, there's a **Spec Document System** that provides:
- **Document tree structure**: Organize specs hierarchically (e.g., "Company Agents" → "Support" → "Billing Agent")
- **Agent linking**: Link any document to an agent - changes sync automatically to the agent's spec
- **Version history**: Every change creates a new version with full history and rollback
- **Unified view**: Render the entire document tree as a single markdown document for human review

**Spec Document Tools:**
- `list_spec_documents` - List all spec documents
- `get_spec_document` - Get a document with its content
- `create_spec_document` - Create a new document (root or child)
- `update_spec_document` - Update content (auto-versions)
- `link_spec_to_agent` - Link a document to an agent
- `unlink_spec_from_agent` - Remove the link
- `get_spec_document_history` - View version history
- `restore_spec_document_version` - Rollback to a previous version
- `delete_spec_document` - Delete a document (and children)
- `render_full_spec` - Render all documents as one markdown file

**Example structure:**
```
Company AI Agents (root document)
├── Customer Support
│   ├── Billing Support → linked to billing-agent
│   └── Technical Support → linked to tech-agent
├── Internal Tools
│   └── HR Assistant → linked to hr-agent
└── Guidelines (shared context for all agents)
```

When helping users:
- Ask clarifying questions to understand what they want their agent to do
- Suggest appropriate system prompts based on the agent's purpose
- Recommend tools that would be useful for the agent's tasks
- Help them add relevant knowledge/context
- Explain the impact of different model choices and settings
- **Proactively suggest scanning for tools** when users describe functionality that might exist in their codebase
- **Suggest multi-agent patterns** when the user describes complex workflows that could benefit from specialized agents
- **Offer to switch agents** when the user mentions wanting to work on a different agent

Be conversational and helpful. Guide users through the process step by step.

## CRITICAL: Distinguish Instructions from Examples

**Before taking action, carefully determine whether the user is:**
1. **Giving you instructions** to modify agents
2. **Showing you example output** from an agent conversation
3. **Describing a problem** they observed and want to discuss

**Signs that text is EXAMPLE OUTPUT (not instructions):**
- Quoted conversation transcripts
- Text that reads like an agent responding to a user
- Phrases like "this was the output", "the agent said", "here's what happened"
- Multiple back-and-forth exchanges between user/assistant roles

**When you see example output or conversation transcripts:**
- Do NOT immediately start modifying agents based on the content
- ASK the user what they want you to do with this information
- Example: "I see you've shared a conversation from the S'Ai system. What would you like me to help with? Are you asking me to modify how these agents behave, or are you describing an issue you'd like to discuss?"

## CRITICAL: Confirm Before Bulk Changes

**Before making changes to multiple agents:**
- Summarize what you're about to do
- List which agents will be affected
- Ask for explicit confirmation
- Example: "I understand you want to update 5 agents to present as a unified system. This will modify: stage-assessor, state-assessor, epistemic-validator, integration-planner, and guardrail-monitor. Should I proceed?"

**Be conservative with ambiguous requests.** When in doubt, ask for clarification rather than taking action.

## IMPORTANT: Always Provide Clear Summaries

### After Individual Actions
After completing any actions (creating agents, updating prompts, adding tools, etc.), briefly mention what you did:
- "I've updated the system prompt to make the agent respond in pirate speak."
- "I've added the search_orders tool to the agent."

### After Completing a Task or Request
When you've finished fulfilling a user's request (especially multi-step tasks), ALWAYS provide a comprehensive **Task Completion Summary** that includes:

1. **What was accomplished**: A clear statement of what you achieved
2. **Changes made**: List the specific modifications (agents created, prompts updated, tools added, etc.)
3. **Current state**: Brief description of how the agent/system is now configured
4. **Next steps** (if applicable): Suggestions for testing or further improvements

**Example Task Completion Summary:**
```
## ✅ Task Complete

I've set up your Customer Support system with the following:

**Created:**
- Customer Support Bot (customer-support) - Main entry point
- Billing Specialist (billing-specialist) - Handles payment questions
- Tech Support (tech-support) - Handles technical issues

**Configured:**
- Added sub-agent routing to the main bot
- Each specialist has domain-specific system prompts
- All agents share access to the knowledge base

**Ready to test:** Try asking the Customer Support Bot about a billing issue - it should route to the Billing Specialist.
```

This summary format helps users understand exactly what was built and how to use it.

Current agent being edited: {agent_context}
"""

BUILDER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_agent",
            "description": "Create a new agent with the given name and description. Use this when no agent is selected or when the user wants to create a new agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name for the new agent (e.g., 'Tony', 'Customer Support Bot')",
                    },
                    "description": {
                        "type": "string",
                        "description": "A brief description of what the agent does",
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Optional initial system prompt. Can be updated later.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_system_prompt",
            "description": "Update the agent's system prompt. This defines the agent's personality, role, and behavior.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_prompt": {
                        "type": "string",
                        "description": "The new system prompt for the agent",
                    },
                },
                "required": ["system_prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_agent_name",
            "description": "Update the agent's name and description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The new name for the agent",
                    },
                    "description": {
                        "type": "string",
                        "description": "A brief description of what the agent does",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_agent_spec",
            "description": "Get the agent's specification - a human-readable description of the agent's intended behavior, capabilities, and constraints. The spec is separate from the technical system prompt and is meant for human oversight and documentation.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_agent_spec",
            "description": "Update the agent's specification. The spec should describe in plain English: what the agent does, what it should and shouldn't do, its personality/tone, and any important constraints. This is for human oversight - non-technical stakeholders can review and edit this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spec": {
                        "type": "string",
                        "description": "The agent specification in plain English. Describe the agent's purpose, capabilities, constraints, and expected behavior.",
                    },
                },
                "required": ["spec"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_model_settings",
            "description": "Update the agent's model and settings (temperature, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "The LLM model to use (e.g., 'gpt-4o', 'gpt-4o-mini', 'claude-3-opus')",
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature setting (0-2). Lower = more focused, higher = more creative",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_memory_enabled",
            "description": "Enable or disable conversation memory for the agent. When enabled (default), the agent can remember facts about users across messages using the 'remember' tool. Memory only works for authenticated users.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether to enable memory. True = agent can remember facts, False = no memory.",
                    },
                },
                "required": ["enabled"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory_status",
            "description": "Check if memory is enabled for the current agent.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "configure_memory",
            "description": "Configure advanced memory settings for the agent. Memory allows agents to remember facts about users across conversations with different scopes: 'conversation' (this chat only), 'user' (persists across chats), 'system' (shared with other agents).",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether memory is enabled. Default: true",
                    },
                    "default_scope": {
                        "type": "string",
                        "enum": ["conversation", "user", "system"],
                        "description": "Default scope for new memories. 'conversation' = this chat only, 'user' = persists across chats, 'system' = shared with other agents. Default: 'user'",
                    },
                    "allowed_scopes": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["conversation", "user", "system"]},
                        "description": "Which scopes the agent can use. Default: all scopes",
                    },
                    "auto_recall": {
                        "type": "boolean",
                        "description": "Whether to automatically recall memories at the start of conversations. Default: true",
                    },
                    "max_memories_in_prompt": {
                        "type": "integer",
                        "description": "Maximum number of memories to include in the system prompt. Default: 50",
                    },
                    "include_system_memories": {
                        "type": "boolean",
                        "description": "Whether to include system-scoped memories from other agents. Default: true",
                    },
                    "retention_days": {
                        "type": "integer",
                        "description": "Number of days to retain memories. Null = forever. Default: null",
                    },
                },
            },
        },
    },
    # Spec Document tools
    {
        "type": "function",
        "function": {
            "name": "list_spec_documents",
            "description": "List all spec documents, optionally filtered. Returns the document tree structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_only": {
                        "type": "boolean",
                        "description": "If true, only return root documents (no parent). Default: false",
                    },
                    "linked_only": {
                        "type": "boolean",
                        "description": "If true, only return documents linked to agents. Default: false",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spec_document",
            "description": "Get a spec document by ID, including its content and metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document to retrieve",
                    },
                    "include_children": {
                        "type": "boolean",
                        "description": "If true, include all descendant documents. Default: false",
                    },
                    "render_as_markdown": {
                        "type": "boolean",
                        "description": "If true, render the document tree as a single markdown document. Default: false",
                    },
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_spec_document",
            "description": "Create a new spec document. Can be a root document or a child of an existing document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title",
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown content of the document",
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Optional: UUID of parent document. If not provided, creates a root document.",
                    },
                    "linked_agent_id": {
                        "type": "string",
                        "description": "Optional: UUID of agent to link this document to. The document content will sync to the agent's spec.",
                    },
                    "order": {
                        "type": "integer",
                        "description": "Optional: Order among siblings. Default: 0",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_spec_document",
            "description": "Update a spec document's content or metadata. Creates a new version automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)",
                    },
                    "content": {
                        "type": "string",
                        "description": "New markdown content (optional)",
                    },
                    "order": {
                        "type": "integer",
                        "description": "New order among siblings (optional)",
                    },
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "link_spec_to_agent",
            "description": "Link a spec document to an agent. The document's content will sync to the agent's spec field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "The UUID of the agent to link to. Use 'current' for the agent being edited.",
                    },
                },
                "required": ["document_id", "agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unlink_spec_from_agent",
            "description": "Remove the link between a spec document and its agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document to unlink",
                    },
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spec_document_history",
            "description": "Get the version history of a spec document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of versions to return. Default: 10",
                    },
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restore_spec_document_version",
            "description": "Restore a spec document to a previous version. Creates a new version with the restored content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document",
                    },
                    "version_number": {
                        "type": "integer",
                        "description": "The version number to restore to",
                    },
                },
                "required": ["document_id", "version_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_spec_document",
            "description": "Delete a spec document. If it has children, they will also be deleted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "The UUID of the document to delete",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to confirm deletion",
                    },
                },
                "required": ["document_id", "confirm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_full_spec",
            "description": "Render all spec documents (or a subtree) as a single unified markdown document for human review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_document_id": {
                        "type": "string",
                        "description": "Optional: Start from this document. If not provided, renders all root documents.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_knowledge",
            "description": "Add a knowledge source to the agent. Use inclusion_mode='always' for small context that should always be included, or 'rag' for larger documents that should be searched.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name/title for this knowledge source",
                    },
                    "content": {
                        "type": "string",
                        "description": "The knowledge content (text)",
                    },
                    "inclusion_mode": {
                        "type": "string",
                        "enum": ["always", "rag"],
                        "description": "How to include this knowledge: 'always' (in every prompt) or 'rag' (retrieved based on relevance). Default: 'always'",
                    },
                },
                "required": ["name", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "index_knowledge",
            "description": "Index RAG knowledge sources for similarity search. Call this after adding knowledge with inclusion_mode='rag'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "knowledge_id": {
                        "type": "string",
                        "description": "Optional: specific knowledge ID to index. If not provided, indexes all pending RAG knowledge.",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force re-indexing even if already indexed. Default: false",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rag_status",
            "description": "Get the indexing status of RAG knowledge sources for the agent.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "preview_rag_search",
            "description": "Preview what knowledge would be retrieved for a given query. Useful for testing RAG configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to test",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return. Default: 5",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_rag_config",
            "description": "Update the RAG configuration for the agent (top_k, similarity_threshold, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable or disable RAG for this agent",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of chunks to retrieve. Default: 5",
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0-1). Default: 0.7",
                    },
                    "chunk_size": {
                        "type": "integer",
                        "description": "Size of text chunks in characters. Default: 500",
                    },
                    "chunk_overlap": {
                        "type": "integer",
                        "description": "Overlap between chunks. Default: 50",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_file_config",
            "description": "Update the file upload and processing configuration for the agent. Controls what files users can upload and how they are processed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable or disable file uploads for this agent",
                    },
                    "max_file_size_mb": {
                        "type": "integer",
                        "description": "Maximum file size in megabytes. Default: 100",
                    },
                    "allowed_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of allowed MIME types or patterns (e.g., 'image/*', 'application/pdf', 'text/*'). Default: ['image/*', 'application/pdf', 'text/*']",
                    },
                    "ocr_provider": {
                        "type": "string",
                        "enum": ["tesseract", "google_vision", "aws_textract", "azure_di", None],
                        "description": "OCR provider for text extraction from images/PDFs. Options: tesseract (local), google_vision, aws_textract, azure_di. Set to null to disable OCR.",
                    },
                    "vision_provider": {
                        "type": "string",
                        "enum": ["openai", "anthropic", "gemini", None],
                        "description": "AI vision provider for image understanding. Options: openai (GPT-4V), anthropic (Claude Vision), gemini. Set to null to disable vision.",
                    },
                    "enable_thumbnails": {
                        "type": "boolean",
                        "description": "Generate thumbnails for uploaded images. Default: true",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_config",
            "description": "Get the current configuration of the agent being edited.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    # Dynamic Tool Inspector tools
    {
        "type": "function",
        "function": {
            "name": "scan_project_for_tools",
            "description": "Scan the Django project to discover functions that can be used as tools. Returns a list of discovered functions with their signatures and descriptions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of app names to scan. If not provided, scans all project apps.",
                    },
                    "include_private": {
                        "type": "boolean",
                        "description": "Whether to include private functions (starting with _). Default: false",
                    },
                    "directory": {
                        "type": "string",
                        "description": "Optional specific directory to scan instead of Django apps.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_discovered_functions",
            "description": "List functions that were discovered from the most recent scan. Can filter by type, module, or side effects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_type": {
                        "type": "string",
                        "enum": ["function", "method", "view", "model_method", "manager_method", "utility"],
                        "description": "Filter by function type",
                    },
                    "module_filter": {
                        "type": "string",
                        "description": "Filter by module path (partial match)",
                    },
                    "safe_only": {
                        "type": "boolean",
                        "description": "Only show functions without side effects",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Default: 50",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_tool_from_function",
            "description": "Add a discovered function as a dynamic tool to the agent. The function will be callable by the agent at runtime.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_path": {
                        "type": "string",
                        "description": "Full import path to the function (e.g., 'myapp.utils.calculate_tax')",
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Optional custom name for the tool. If not provided, derives from function name.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional custom description. If not provided, uses function docstring.",
                    },
                    "requires_confirmation": {
                        "type": "boolean",
                        "description": "Whether to require user confirmation before execution. Default: true for functions with side effects.",
                    },
                },
                "required": ["function_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_agent_tools",
            "description": "List all tools currently assigned to the agent, including both static and dynamic tools.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Whether to include inactive tools. Default: false",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_tool",
            "description": "Remove a tool from the agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to remove",
                    },
                    "tool_id": {
                        "type": "string",
                        "description": "UUID of the tool to remove (alternative to tool_name)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_function_details",
            "description": "Get detailed information about a specific discovered function, including its full signature, docstring, and parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_path": {
                        "type": "string",
                        "description": "Full import path to the function (e.g., 'myapp.utils.calculate_tax')",
                    },
                },
                "required": ["function_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_revisions",
            "description": "List all revisions (version history) for the agent. Shows when changes were made and what changed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of revisions to return. Default: 20",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_revision",
            "description": "Get the full configuration snapshot from a specific revision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "revision_number": {
                        "type": "integer",
                        "description": "The revision number to retrieve",
                    },
                },
                "required": ["revision_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restore_revision",
            "description": "Restore the agent to a previous revision. This creates a new revision with the old configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "revision_number": {
                        "type": "integer",
                        "description": "The revision number to restore",
                    },
                },
                "required": ["revision_number"],
            },
        },
    },
    # ==========================================================================
    # Multi-Agent / Sub-Agent Tools
    # ==========================================================================
    {
        "type": "function",
        "function": {
            "name": "list_available_agents",
            "description": "List all available agents that can be used as sub-agents. Returns agents that the current agent can delegate to.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Whether to include inactive agents. Default: false",
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter agents by name or description",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_sub_agent_tool",
            "description": "Add another agent as a sub-agent tool. This allows the current agent to delegate tasks to the sub-agent. Requires CREATOR or ADMIN permission level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sub_agent_slug": {
                        "type": "string",
                        "description": "The slug of the agent to add as a sub-agent (e.g., 'billing-specialist')",
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "The name for this sub-agent tool (e.g., 'billing_specialist'). Should be snake_case.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of when to use this sub-agent (e.g., 'Consult for billing and payment questions')",
                    },
                    "context_mode": {
                        "type": "string",
                        "enum": ["message_only", "summary", "full"],
                        "description": "How much context to pass to the sub-agent. 'message_only' (default): just the task message. 'summary': brief context summary. 'full': entire conversation history.",
                    },
                },
                "required": ["sub_agent_slug", "tool_name", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_sub_agent_tools",
            "description": "List all sub-agent tools configured for the current agent.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_sub_agent_tool",
            "description": "Remove a sub-agent tool from the current agent. Requires CREATOR or ADMIN permission level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "The name of the sub-agent tool to remove",
                    },
                },
                "required": ["tool_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_sub_agent_tool",
            "description": "Update a sub-agent tool's configuration (description, context_mode). Requires CREATOR or ADMIN permission level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "The name of the sub-agent tool to update",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the sub-agent tool",
                    },
                    "context_mode": {
                        "type": "string",
                        "enum": ["message_only", "summary", "full"],
                        "description": "New context mode for the sub-agent",
                    },
                },
                "required": ["tool_name"],
            },
        },
    },
    # ==========================================================================
    # UI Control Tools - Allow builder to switch agents/systems in the UI
    # ==========================================================================
    {
        "type": "function",
        "function": {
            "name": "switch_to_agent",
            "description": "Switch the UI to edit a different agent. This changes which agent is being edited in the builder interface.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_slug": {
                        "type": "string",
                        "description": "The slug of the agent to switch to (e.g., 'billing-specialist')",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "The UUID of the agent to switch to (alternative to slug)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "switch_to_system",
            "description": "Switch the UI to work with a multi-agent system. This selects a system in the builder interface.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_slug": {
                        "type": "string",
                        "description": "The slug of the system to switch to (e.g., 'customer-support')",
                    },
                    "system_id": {
                        "type": "string",
                        "description": "The UUID of the system to switch to (alternative to slug)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_agents",
            "description": "List all available agents in the system. Use this to find agents to switch to or to see what agents exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Whether to include inactive agents. Default: false",
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter agents by name or description",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_systems",
            "description": "List all available multi-agent systems. Use this to find systems to switch to or to see what systems exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Whether to include inactive systems. Default: false",
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter systems by name or description",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_details",
            "description": "Get detailed information about a multi-agent system, including its members and configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_slug": {
                        "type": "string",
                        "description": "The slug of the system to get details for",
                    },
                    "system_id": {
                        "type": "string",
                        "description": "The UUID of the system (alternative to slug)",
                    },
                },
            },
        },
    },
    # ==========================================================================
    # System Management Tools - Create, modify, and delete multi-agent systems
    # ==========================================================================
    {
        "type": "function",
        "function": {
            "name": "create_system",
            "description": "Create a new multi-agent system. A system groups related agents that work together, with one agent as the entry point that handles initial requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Human-readable name for the system (e.g., 'Customer Support')",
                    },
                    "slug": {
                        "type": "string",
                        "description": "Unique identifier slug (e.g., 'customer-support'). If not provided, will be generated from name.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this system does",
                    },
                    "entry_agent_slug": {
                        "type": "string",
                        "description": "Slug of the agent that handles initial requests (entry point)",
                    },
                    "auto_discover": {
                        "type": "boolean",
                        "description": "If true, automatically discover and add all sub-agents reachable from the entry agent. Default: true",
                    },
                },
                "required": ["name", "entry_agent_slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_agent_to_system",
            "description": "Add an agent to a multi-agent system as a member.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_slug": {
                        "type": "string",
                        "description": "Slug of the system to add the agent to",
                    },
                    "agent_slug": {
                        "type": "string",
                        "description": "Slug of the agent to add",
                    },
                    "role": {
                        "type": "string",
                        "enum": ["specialist", "utility", "supervisor"],
                        "description": "Role of the agent in the system. Default: 'specialist'",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about this agent's role in the system",
                    },
                },
                "required": ["system_slug", "agent_slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_agent_from_system",
            "description": "Remove an agent from a multi-agent system. Cannot remove the entry point agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_slug": {
                        "type": "string",
                        "description": "Slug of the system to remove the agent from",
                    },
                    "agent_slug": {
                        "type": "string",
                        "description": "Slug of the agent to remove",
                    },
                },
                "required": ["system_slug", "agent_slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_system_config",
            "description": "Update a multi-agent system's configuration including name, description, entry agent, and shared knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_slug": {
                        "type": "string",
                        "description": "Slug of the system to update",
                    },
                    "name": {
                        "type": "string",
                        "description": "New name for the system",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description for the system",
                    },
                    "entry_agent_slug": {
                        "type": "string",
                        "description": "Slug of the new entry point agent (must be a member of the system)",
                    },
                    "is_active": {
                        "type": "boolean",
                        "description": "Whether the system is active",
                    },
                    "shared_knowledge": {
                        "type": "array",
                        "description": "Shared knowledge items for all agents in the system. Each item has: key, title, content, inject_as ('system'|'context'|'knowledge'), priority, enabled",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string", "description": "Unique key for this knowledge item"},
                                "title": {"type": "string", "description": "Title/name of the knowledge"},
                                "content": {"type": "string", "description": "The knowledge content"},
                                "inject_as": {
                                    "type": "string",
                                    "enum": ["system", "context", "knowledge"],
                                    "description": "How to inject: 'system' (prepend to system prompt), 'context' (add as context), 'knowledge' (RAG searchable)",
                                },
                                "priority": {"type": "integer", "description": "Priority order (lower = higher priority)"},
                                "enabled": {"type": "boolean", "description": "Whether this knowledge is active"},
                            },
                        },
                    },
                },
                "required": ["system_slug"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_system",
            "description": "Delete a multi-agent system. This removes the system and all its member associations, but does NOT delete the agents themselves.",
            "parameters": {
                "type": "object",
                "properties": {
                    "system_slug": {
                        "type": "string",
                        "description": "Slug of the system to delete",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to confirm deletion",
                    },
                },
                "required": ["system_slug", "confirm"],
            },
        },
    },
]


class BuilderAgentRuntime(AgentRuntime):
    """
    The agent builder assistant that helps users create custom agents.
    
    This agent has tools to modify AgentDefinition objects and guides
    users through the agent creation process.
    """
    
    @property
    def key(self) -> str:
        return "agent-builder"
    
    async def run(self, ctx: RunContext) -> RunResult:
        """Execute the builder agent with agentic loop."""
        # Get the agent being edited from context
        # Check both metadata (from frontend) and params (from API)
        initial_agent_id = ctx.metadata.get("agent_id") or ctx.params.get("agent_id")
        agent_context = "No agent selected. Ask the user what kind of agent they want to create."

        # Use a mutable container so switch_to_agent can update the current agent
        # This allows the builder to work on different agents during a single run
        current_agent = {"id": initial_agent_id}

        if initial_agent_id:
            try:
                agent = await sync_to_async(AgentDefinition.objects.get)(id=initial_agent_id)
                config = await sync_to_async(agent.get_effective_config)()
                agent_context = f"""
Agent: {agent.name} ({agent.slug})
Description: {agent.description or 'Not set'}
Model: {config.get('model', 'gpt-4o')}
System Prompt: {config.get('system_prompt', 'Not set')[:500]}...
Tools: {len(config.get('tools', []))} configured
Knowledge: {len(config.get('knowledge', []))} sources
"""
            except AgentDefinition.DoesNotExist:
                agent_context = "Agent not found. A new agent will be created."

        # Build messages
        system_prompt = BUILDER_SYSTEM_PROMPT.format(agent_context=agent_context)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(ctx.input_messages)

        # Get model from params (allows per-request override) or use default
        model = ctx.params.get("model", DEFAULT_MODEL)

        # Get LLM client for the specified model (auto-detects provider)
        llm = get_llm_client_for_model(model)

        # Create tool executor function for the agentic loop
        # Uses current_agent dict so switch_to_agent can update which agent we're working on
        async def execute_tool(tool_name: str, tool_args: dict) -> dict:
            return await self._execute_tool(current_agent, tool_name, tool_args, ctx)

        # Use the shared agentic loop
        # Note: agentic_loop emits ASSISTANT_MESSAGE for the final response
        # ensure_final_response=True ensures a summary is generated if tools were used
        result = await run_agentic_loop(
            llm=llm,
            messages=messages,
            tools=BUILDER_TOOLS,
            execute_tool=execute_tool,
            ctx=ctx,
            model=model,
            max_iterations=10,
            temperature=0.7,
            ensure_final_response=True,
        )

        return RunResult(
            final_output={"response": result.final_content},
            final_messages=result.messages,
        )
    
    async def _execute_tool(
        self,
        current_agent: dict,
        tool_name: str,
        args: dict,
        ctx: RunContext,
    ) -> dict:
        """Execute a builder tool.

        Args:
            current_agent: Mutable dict with 'id' key tracking the current agent.
                          This allows switch_to_agent to update which agent we're working on.
            tool_name: Name of the tool to execute
            args: Tool arguments
            ctx: Run context
        """
        # Import here to avoid circular imports
        from django_agent_runtime.models import AgentKnowledge, DynamicTool
        from django_agent_runtime.dynamic_tools.scanner import ProjectScanner
        from django_agent_runtime.dynamic_tools.generator import ToolGenerator

        agent_id = current_agent.get("id")
        logger.info(f"_execute_tool: {tool_name} with current_agent={current_agent}")

        # Tools that don't require an agent
        if tool_name == "scan_project_for_tools":
            return await self._scan_project_for_tools(args, ctx)

        if tool_name == "list_discovered_functions":
            return await self._list_discovered_functions(args, ctx)

        if tool_name == "get_function_details":
            return await self._get_function_details(args, ctx)

        if tool_name == "create_agent":
            result = await self._create_agent(args, ctx)
            # If agent was created successfully, update current_agent to point to it
            if result.get("success") and result.get("agent_id"):
                current_agent["id"] = result["agent_id"]
                logger.info(f"Updated current_agent to newly created agent: {result['agent_id']}")
            return result

        # UI Control tools - these emit special events to control the frontend
        if tool_name == "switch_to_agent":
            result = await self._switch_to_agent(args, ctx)
            # If switch was successful, update current_agent to the new agent
            if result.get("success") and result.get("agent_id"):
                current_agent["id"] = result["agent_id"]
                logger.info(f"Updated current_agent to switched agent: {result['agent_id']}")
            return result

        if tool_name == "switch_to_system":
            return await self._switch_to_system(args, ctx)

        if tool_name == "list_all_agents":
            return await self._list_all_agents(args, ctx)

        if tool_name == "list_all_systems":
            return await self._list_all_systems(args, ctx)

        if tool_name == "get_system_details":
            return await self._get_system_details(args, ctx)

        # System management tools
        if tool_name == "create_system":
            return await self._create_system(args, ctx)

        if tool_name == "add_agent_to_system":
            return await self._add_agent_to_system(args, ctx)

        if tool_name == "remove_agent_from_system":
            return await self._remove_agent_from_system(args, ctx)

        if tool_name == "update_system_config":
            return await self._update_system_config(args, ctx)

        if tool_name == "delete_system":
            return await self._delete_system(args, ctx)

        # Tools that require an agent
        if not agent_id:
            return {"error": "No agent selected. Please create an agent first or use create_agent tool."}

        try:
            agent = await sync_to_async(AgentDefinition.objects.get)(id=agent_id)
            version = await sync_to_async(agent.versions.filter(is_active=True).first)()

            if tool_name == "get_current_config":
                return await sync_to_async(agent.get_effective_config)()

            elif tool_name == "update_system_prompt":
                if "system_prompt" not in args:
                    return {
                        "error": "Missing required parameter: system_prompt",
                        "hint": "You must provide the full new system_prompt text. Example: update_system_prompt({\"system_prompt\": \"You are a helpful pirate assistant...\"})"
                    }
                if version:
                    version.system_prompt = args["system_prompt"]
                    await sync_to_async(version.save)()
                    await create_revision(agent, comment="Updated system prompt")
                    return {"success": True, "message": "System prompt updated"}
                return {"error": "No active version found"}

            elif tool_name == "update_agent_name":
                old_name = agent.name
                agent.name = args["name"]
                if "description" in args:
                    agent.description = args["description"]
                await sync_to_async(agent.save)()
                await create_revision(agent, comment=f"Renamed from '{old_name}' to '{agent.name}'")
                return {"success": True, "message": "Agent name updated"}

            elif tool_name == "get_agent_spec":
                # Get spec from linked SpecDocument
                from django_agent_runtime.models import SpecDocument
                spec_doc = await sync_to_async(
                    lambda: SpecDocument.objects.filter(linked_agent=agent).first()
                )()
                spec_content = spec_doc.content if spec_doc else ""
                return {
                    "spec": spec_content,
                    "has_spec": bool(spec_content),
                    "spec_document_id": str(spec_doc.id) if spec_doc else None,
                    "spec_document_title": spec_doc.title if spec_doc else None,
                    "message": "The agent spec describes intended behavior in plain English, separate from the technical system prompt.",
                }

            elif tool_name == "update_agent_spec":
                # Update or create linked SpecDocument
                from django_agent_runtime.models import SpecDocument
                logger.info(f"update_agent_spec called for agent {agent.id} ({agent.slug})")

                spec_content = args["spec"]

                # Find or create the spec document for this agent
                def update_or_create_spec():
                    spec_doc = SpecDocument.objects.filter(linked_agent=agent).first()
                    if spec_doc:
                        # Update existing document
                        spec_doc.content = spec_content
                        spec_doc.save()  # This auto-creates a version
                        return spec_doc, False
                    else:
                        # Create new document
                        spec_doc = SpecDocument.objects.create(
                            title=f"{agent.name} Specification",
                            content=spec_content,
                            linked_agent=agent,
                            owner=agent.owner,
                        )
                        return spec_doc, True

                spec_doc, created = await sync_to_async(update_or_create_spec)()
                logger.info(f"{'Created' if created else 'Updated'} spec document {spec_doc.id} for agent {agent.id}")

                await create_revision(agent, comment="Updated agent specification")
                return {
                    "success": True,
                    "message": f"Agent specification {'created' if created else 'updated'} for '{agent.name}' ({agent.slug})",
                    "agent_id": str(agent.id),
                    "agent_slug": agent.slug,
                    "spec_document_id": str(spec_doc.id),
                    "spec_preview": spec_content[:200] + "..." if len(spec_content) > 200 else spec_content,
                }

            elif tool_name == "update_model_settings":
                if version:
                    changes = []
                    if "model" in args:
                        version.model = args["model"]
                        changes.append(f"model={args['model']}")
                    if "temperature" in args:
                        version.model_settings["temperature"] = args["temperature"]
                        changes.append(f"temperature={args['temperature']}")
                    await sync_to_async(version.save)()
                    await create_revision(agent, comment=f"Updated model settings: {', '.join(changes)}")
                    return {"success": True, "message": "Model settings updated"}
                return {"error": "No active version found"}

            elif tool_name == "set_memory_enabled":
                if version:
                    enabled = args.get("enabled", True)
                    if version.extra_config is None:
                        version.extra_config = {}
                    version.extra_config["memory_enabled"] = enabled
                    await sync_to_async(version.save)()
                    status = "enabled" if enabled else "disabled"
                    await create_revision(agent, comment=f"Memory {status}")
                    return {
                        "success": True,
                        "message": f"Memory {status} for this agent",
                        "memory_enabled": enabled,
                    }
                return {"error": "No active version found"}

            elif tool_name == "get_memory_status":
                if version:
                    extra = version.extra_config or {}
                    enabled = extra.get("memory_enabled", True)  # Default is True
                    default_scope = extra.get("memory_default_scope", "user")
                    allowed_scopes = extra.get("memory_allowed_scopes", ["conversation", "user", "system"])
                    auto_recall = extra.get("memory_auto_recall", True)
                    max_in_prompt = extra.get("memory_max_in_prompt", 50)
                    include_system = extra.get("memory_include_system", True)
                    retention_days = extra.get("memory_retention_days", None)
                    return {
                        "memory_enabled": enabled,
                        "default_scope": default_scope,
                        "allowed_scopes": allowed_scopes,
                        "auto_recall": auto_recall,
                        "max_memories_in_prompt": max_in_prompt,
                        "include_system_memories": include_system,
                        "retention_days": retention_days,
                        "message": f"Memory is {'enabled' if enabled else 'disabled'} for this agent",
                        "note": "When enabled, the agent has 'remember', 'recall', and 'forget' tools. Memory scopes: 'conversation' (this chat), 'user' (persists), 'system' (shared).",
                    }
                return {"error": "No active version found"}

            elif tool_name == "configure_memory":
                if version:
                    if version.extra_config is None:
                        version.extra_config = {}

                    changes = []
                    if "enabled" in args:
                        version.extra_config["memory_enabled"] = args["enabled"]
                        changes.append(f"enabled={args['enabled']}")
                    if "default_scope" in args:
                        version.extra_config["memory_default_scope"] = args["default_scope"]
                        changes.append(f"default_scope={args['default_scope']}")
                    if "allowed_scopes" in args:
                        version.extra_config["memory_allowed_scopes"] = args["allowed_scopes"]
                        changes.append(f"allowed_scopes={args['allowed_scopes']}")
                    if "auto_recall" in args:
                        version.extra_config["memory_auto_recall"] = args["auto_recall"]
                        changes.append(f"auto_recall={args['auto_recall']}")
                    if "max_memories_in_prompt" in args:
                        version.extra_config["memory_max_in_prompt"] = args["max_memories_in_prompt"]
                        changes.append(f"max_memories={args['max_memories_in_prompt']}")
                    if "include_system_memories" in args:
                        version.extra_config["memory_include_system"] = args["include_system_memories"]
                        changes.append(f"include_system={args['include_system_memories']}")
                    if "retention_days" in args:
                        version.extra_config["memory_retention_days"] = args["retention_days"]
                        changes.append(f"retention_days={args['retention_days']}")

                    await sync_to_async(version.save)()
                    await create_revision(agent, comment=f"Memory config: {', '.join(changes)}")

                    # Return current config
                    extra = version.extra_config
                    return {
                        "success": True,
                        "message": f"Memory configuration updated: {', '.join(changes)}",
                        "config": {
                            "enabled": extra.get("memory_enabled", True),
                            "default_scope": extra.get("memory_default_scope", "user"),
                            "allowed_scopes": extra.get("memory_allowed_scopes", ["conversation", "user", "system"]),
                            "auto_recall": extra.get("memory_auto_recall", True),
                            "max_memories_in_prompt": extra.get("memory_max_in_prompt", 50),
                            "include_system_memories": extra.get("memory_include_system", True),
                            "retention_days": extra.get("memory_retention_days", None),
                        },
                    }
                return {"error": "No active version found"}

            # Spec Document tools
            elif tool_name == "list_spec_documents":
                return await self._list_spec_documents(agent, args, ctx)

            elif tool_name == "get_spec_document":
                return await self._get_spec_document(agent, args, ctx)

            elif tool_name == "create_spec_document":
                return await self._create_spec_document(agent, args, ctx)

            elif tool_name == "update_spec_document":
                return await self._update_spec_document(agent, args, ctx)

            elif tool_name == "link_spec_to_agent":
                return await self._link_spec_to_agent(agent, args, ctx)

            elif tool_name == "unlink_spec_from_agent":
                return await self._unlink_spec_from_agent(agent, args, ctx)

            elif tool_name == "get_spec_document_history":
                return await self._get_spec_document_history(agent, args, ctx)

            elif tool_name == "restore_spec_document_version":
                return await self._restore_spec_document_version(agent, args, ctx)

            elif tool_name == "delete_spec_document":
                return await self._delete_spec_document(agent, args, ctx)

            elif tool_name == "render_full_spec":
                return await self._render_full_spec(agent, args, ctx)

            elif tool_name == "add_knowledge":
                inclusion_mode = args.get("inclusion_mode", "always")
                knowledge = await sync_to_async(AgentKnowledge.objects.create)(
                    agent=agent,
                    name=args["name"],
                    knowledge_type="text",
                    content=args["content"],
                    inclusion_mode=inclusion_mode,
                )
                await create_revision(agent, comment=f"Added knowledge: {args['name']} ({inclusion_mode})")

                result = {
                    "success": True,
                    "message": f"Knowledge '{args['name']}' added with mode '{inclusion_mode}'",
                    "knowledge_id": str(knowledge.id),
                }

                # If RAG mode, remind to index
                if inclusion_mode == "rag":
                    result["note"] = "Use index_knowledge to index this knowledge for RAG search."

                return result

            elif tool_name == "index_knowledge":
                return await self._index_knowledge(agent, args, ctx)

            elif tool_name == "get_rag_status":
                return await self._get_rag_status(agent, args, ctx)

            elif tool_name == "preview_rag_search":
                return await self._preview_rag_search(agent, args, ctx)

            elif tool_name == "update_rag_config":
                return await self._update_rag_config(agent, args, ctx)

            elif tool_name == "update_file_config":
                return await self._update_file_config(agent, args, ctx)

            elif tool_name == "add_tool_from_function":
                return await self._add_tool_from_function(agent, args, ctx)

            elif tool_name == "list_agent_tools":
                return await self._list_agent_tools(agent, args, ctx)

            elif tool_name == "remove_tool":
                return await self._remove_tool(agent, args, ctx)

            elif tool_name == "list_revisions":
                return await self._list_revisions(agent, args, ctx)

            elif tool_name == "get_revision":
                return await self._get_revision(agent, args, ctx)

            elif tool_name == "restore_revision":
                return await self._restore_revision(agent, args, ctx)

            # Multi-agent / Sub-agent tools
            elif tool_name == "list_available_agents":
                return await self._list_available_agents(agent, args, ctx)

            elif tool_name == "add_sub_agent_tool":
                return await self._add_sub_agent_tool(agent, args, ctx)

            elif tool_name == "list_sub_agent_tools":
                return await self._list_sub_agent_tools(agent, args, ctx)

            elif tool_name == "remove_sub_agent_tool":
                return await self._remove_sub_agent_tool(agent, args, ctx)

            elif tool_name == "update_sub_agent_tool":
                return await self._update_sub_agent_tool(agent, args, ctx)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except AgentDefinition.DoesNotExist:
            return {"error": "Agent not found"}
        except Exception as e:
            logger.exception(f"Error executing builder tool {tool_name}")
            return {"error": str(e)}

    async def _create_agent(self, args: dict, ctx: RunContext) -> dict:
        """Create a new agent with the given name and description."""
        from django.utils.text import slugify

        name = args.get("name", "New Agent")
        description = args.get("description", "")
        system_prompt = args.get("system_prompt", "You are a helpful assistant.")

        # Generate a unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while await sync_to_async(AgentDefinition.objects.filter(slug=slug).exists)():
            slug = f"{base_slug}-{counter}"
            counter += 1

        try:
            # Create the agent
            agent = await sync_to_async(AgentDefinition.objects.create)(
                name=name,
                slug=slug,
                description=description,
                is_active=True,
            )

            # Create the initial version
            await sync_to_async(AgentVersion.objects.create)(
                agent=agent,
                version="1.0",
                system_prompt=system_prompt,
                model="gpt-4o",
                is_active=True,
                is_draft=False,
            )

            # Create initial revision
            await create_revision(agent, comment="Initial creation")

            return {
                "success": True,
                "agent_id": str(agent.id),
                "slug": agent.slug,
                "message": f"Created agent '{name}' (slug: {slug}). You can now configure it with tools and knowledge.",
            }
        except Exception as e:
            logger.exception("Error creating agent")
            return {"error": str(e)}

    async def _scan_project_for_tools(self, args: dict, ctx: RunContext) -> dict:
        """Scan the Django project for functions that can be used as tools."""
        from django_agent_runtime.dynamic_tools.scanner import ProjectScanner

        try:
            scanner = ProjectScanner(
                include_private=args.get("include_private", False),
                include_tests=False,
                app_filter=args.get("app_filter"),
            )

            # Scan either a specific directory or all Django apps
            if args.get("directory"):
                functions = scanner.scan_directory(args["directory"])
            else:
                functions = scanner.scan()

            # Store in context for later use
            ctx.state["discovered_functions"] = [f.to_dict() for f in functions]

            # Return summary
            by_type = {}
            for f in functions:
                ftype = f.function_type
                by_type[ftype] = by_type.get(ftype, 0) + 1

            return {
                "success": True,
                "total_discovered": len(functions),
                "by_type": by_type,
                "message": f"Discovered {len(functions)} functions. Use list_discovered_functions to see details.",
            }
        except Exception as e:
            logger.exception("Error scanning project")
            return {"error": str(e)}

    async def _list_discovered_functions(self, args: dict, ctx: RunContext) -> dict:
        """List discovered functions from the most recent scan."""
        functions = ctx.state.get("discovered_functions", [])

        if not functions:
            return {
                "error": "No functions discovered yet. Run scan_project_for_tools first."
            }

        # Apply filters
        filtered = functions

        if args.get("function_type"):
            filtered = [f for f in filtered if f["function_type"] == args["function_type"]]

        if args.get("module_filter"):
            module_filter = args["module_filter"].lower()
            filtered = [f for f in filtered if module_filter in f["module_path"].lower()]

        if args.get("safe_only"):
            filtered = [f for f in filtered if not f["has_side_effects"]]

        # Apply limit
        limit = args.get("limit", 50)
        filtered = filtered[:limit]

        # Return simplified view
        results = []
        for f in filtered:
            results.append({
                "name": f["name"],
                "function_path": f["function_path"],
                "function_type": f["function_type"],
                "signature": f["signature"],
                "has_side_effects": f["has_side_effects"],
                "docstring_preview": (f["docstring"][:100] + "...") if len(f.get("docstring", "")) > 100 else f.get("docstring", ""),
            })

        return {
            "total": len(functions),
            "filtered": len(results),
            "functions": results,
        }

    async def _get_function_details(self, args: dict, ctx: RunContext) -> dict:
        """Get detailed information about a specific function."""
        functions = ctx.state.get("discovered_functions", [])
        function_path = args.get("function_path", "")

        for f in functions:
            if f["function_path"] == function_path:
                return {
                    "found": True,
                    "function": f,
                }

        return {
            "found": False,
            "error": f"Function '{function_path}' not found in discovered functions. Run scan_project_for_tools first.",
        }

    async def _add_tool_from_function(self, agent, args: dict, ctx: RunContext) -> dict:
        """Add a discovered function as a dynamic tool to the agent."""
        from django_agent_runtime.models import DynamicTool
        from django_agent_runtime.dynamic_tools.generator import ToolGenerator

        function_path = args.get("function_path", "")
        functions = ctx.state.get("discovered_functions", [])

        # Find the function in discovered functions
        func_info = None
        for f in functions:
            if f["function_path"] == function_path:
                func_info = f
                break

        if not func_info:
            return {
                "error": f"Function '{function_path}' not found. Run scan_project_for_tools first."
            }

        # Generate tool schema
        generator = ToolGenerator()

        # Determine tool name
        tool_name = args.get("tool_name")
        if not tool_name:
            tool_name = func_info["name"]
            if func_info.get("class_name"):
                tool_name = f"{func_info['class_name'].lower()}_{tool_name}"

        # Determine description
        description = args.get("description")
        if not description:
            description = func_info.get("docstring", "").split("\n\n")[0].strip()
            if not description:
                description = f"Execute {func_info['name'].replace('_', ' ')}"

        # Determine requires_confirmation
        requires_confirmation = args.get("requires_confirmation")
        if requires_confirmation is None:
            requires_confirmation = func_info.get("has_side_effects", True)

        # Build parameters schema from function parameters
        properties = {}
        required = []
        for param in func_info.get("parameters", []):
            param_name = param.get("name", "")
            if param_name.startswith("*"):
                continue

            param_type = "string"
            annotation = param.get("annotation", "")
            if annotation:
                type_map = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}
                param_type = type_map.get(annotation.split("[")[0], "string")

            properties[param_name] = {"type": param_type}
            if not param.get("has_default", False):
                required.append(param_name)

        parameters_schema = {"type": "object", "properties": properties}
        if required:
            parameters_schema["required"] = required

        # Check if tool already exists
        existing = await sync_to_async(DynamicTool.objects.filter(agent=agent, name=tool_name).first)()
        if existing:
            return {
                "error": f"Tool '{tool_name}' already exists for this agent. Remove it first or use a different name."
            }

        # Create the dynamic tool
        tool = await sync_to_async(DynamicTool.objects.create)(
            agent=agent,
            name=tool_name,
            description=description,
            function_path=function_path,
            source_file=func_info.get("file_path", ""),
            source_line=func_info.get("line_number"),
            parameters_schema=parameters_schema,
            is_safe=not func_info.get("has_side_effects", True),
            requires_confirmation=requires_confirmation,
        )

        # Create revision
        await create_revision(agent, comment=f"Added tool: {tool_name}")

        return {
            "success": True,
            "message": f"Tool '{tool_name}' added successfully",
            "tool_id": str(tool.id),
            "tool_name": tool_name,
            "function_path": function_path,
        }

    async def _list_agent_tools(self, agent, args: dict, ctx: RunContext) -> dict:
        """List all tools assigned to the agent."""
        from django_agent_runtime.models import AgentTool, DynamicTool

        include_inactive = args.get("include_inactive", False)

        # Get static tools (AgentTool)
        static_query = agent.tools.all()
        if not include_inactive:
            static_query = static_query.filter(is_active=True)

        static_tools = []
        for tool in await sync_to_async(list)(static_query):
            static_tools.append({
                "id": str(tool.id),
                "name": tool.name,
                "type": "static",
                "tool_type": tool.tool_type,
                "description": tool.description,
                "is_active": tool.is_active,
            })

        # Get dynamic tools (DynamicTool)
        dynamic_query = agent.dynamic_tools.all()
        if not include_inactive:
            dynamic_query = dynamic_query.filter(is_active=True)

        dynamic_tools = []
        for tool in await sync_to_async(list)(dynamic_query):
            dynamic_tools.append({
                "id": str(tool.id),
                "name": tool.name,
                "type": "dynamic",
                "function_path": tool.function_path,
                "description": tool.description,
                "is_active": tool.is_active,
                "is_safe": tool.is_safe,
                "requires_confirmation": tool.requires_confirmation,
            })

        return {
            "static_tools": static_tools,
            "dynamic_tools": dynamic_tools,
            "total_static": len(static_tools),
            "total_dynamic": len(dynamic_tools),
        }

    async def _remove_tool(self, agent, args: dict, ctx: RunContext) -> dict:
        """Remove a tool from the agent."""
        from django_agent_runtime.models import AgentTool, DynamicTool

        tool_name = args.get("tool_name")
        tool_id = args.get("tool_id")

        if not tool_name and not tool_id:
            return {"error": "Either tool_name or tool_id must be provided"}

        # Try to find and remove static tool
        static_query = agent.tools.all()
        if tool_id:
            static_query = static_query.filter(id=tool_id)
        elif tool_name:
            static_query = static_query.filter(name=tool_name)

        static_tool = await sync_to_async(static_query.first)()
        if static_tool:
            name = static_tool.name
            await sync_to_async(static_tool.delete)()
            # Create revision
            await create_revision(agent, comment=f"Removed tool: {name}")
            return {"success": True, "message": f"Static tool '{name}' removed"}

        # Try to find and remove dynamic tool
        dynamic_query = agent.dynamic_tools.all()
        if tool_id:
            dynamic_query = dynamic_query.filter(id=tool_id)
        elif tool_name:
            dynamic_query = dynamic_query.filter(name=tool_name)

        dynamic_tool = await sync_to_async(dynamic_query.first)()
        if dynamic_tool:
            name = dynamic_tool.name
            await sync_to_async(dynamic_tool.delete)()
            # Create revision
            await create_revision(agent, comment=f"Removed tool: {name}")
            return {"success": True, "message": f"Dynamic tool '{name}' removed"}

        return {"error": f"Tool not found: {tool_name or tool_id}"}

    async def _list_revisions(self, agent, args: dict, ctx: RunContext) -> dict:
        """List all revisions for the agent."""
        limit = args.get("limit", 20)

        revisions = await sync_to_async(list)(
            agent.revisions.all()[:limit]
        )

        result = []
        for rev in revisions:
            result.append({
                "revision_number": rev.revision_number,
                "comment": rev.comment,
                "created_at": rev.created_at.isoformat(),
                "created_by": str(rev.created_by) if rev.created_by else None,
            })

        return {
            "revisions": result,
            "total": len(result),
        }

    async def _get_revision(self, agent, args: dict, ctx: RunContext) -> dict:
        """Get a specific revision's content."""
        revision_number = args.get("revision_number")

        if not revision_number:
            return {"error": "revision_number is required"}

        revision = await sync_to_async(
            agent.revisions.filter(revision_number=revision_number).first
        )()

        if not revision:
            return {"error": f"Revision {revision_number} not found"}

        return {
            "revision_number": revision.revision_number,
            "comment": revision.comment,
            "created_at": revision.created_at.isoformat(),
            "content": revision.content,
        }

    async def _restore_revision(self, agent, args: dict, ctx: RunContext) -> dict:
        """Restore the agent to a previous revision."""
        revision_number = args.get("revision_number")

        if not revision_number:
            return {"error": "revision_number is required"}

        revision = await sync_to_async(
            agent.revisions.filter(revision_number=revision_number).first
        )()

        if not revision:
            return {"error": f"Revision {revision_number} not found"}

        # Restore creates a new revision with the old content
        new_revision = await sync_to_async(revision.restore)()

        return {
            "success": True,
            "message": f"Restored to revision {revision_number}",
            "new_revision_number": new_revision.revision_number,
        }

    # ==========================================================================
    # RAG Knowledge Management Tools
    # ==========================================================================

    async def _index_knowledge(self, agent, args: dict, ctx: RunContext) -> dict:
        """Index RAG knowledge sources for similarity search."""
        from django_agent_runtime.rag import KnowledgeIndexer

        try:
            indexer = KnowledgeIndexer()
            knowledge_id = args.get("knowledge_id")
            force = args.get("force", False)

            if knowledge_id:
                # Index specific knowledge
                result = await indexer.index_knowledge(knowledge_id, force=force)
            else:
                # Index all pending RAG knowledge for this agent
                result = await indexer.index_agent_knowledge(str(agent.id), force=force)

            return result

        except Exception as e:
            logger.exception("Error indexing knowledge")
            return {"error": str(e)}

    async def _get_rag_status(self, agent, args: dict, ctx: RunContext) -> dict:
        """Get the indexing status of RAG knowledge sources."""
        from django_agent_runtime.rag import KnowledgeIndexer

        try:
            indexer = KnowledgeIndexer()
            return await indexer.get_indexing_status(str(agent.id))
        except Exception as e:
            logger.exception("Error getting RAG status")
            return {"error": str(e)}

    async def _preview_rag_search(self, agent, args: dict, ctx: RunContext) -> dict:
        """Preview RAG search results for a query."""
        from django_agent_runtime.rag import KnowledgeRetriever

        query = args.get("query")
        if not query:
            return {"error": "query is required"}

        try:
            retriever = KnowledgeRetriever()
            return await retriever.preview_search(
                agent_id=str(agent.id),
                query=query,
                top_k=args.get("top_k", 5),
            )
        except Exception as e:
            logger.exception("Error previewing RAG search")
            return {"error": str(e)}

    async def _update_rag_config(self, agent, args: dict, ctx: RunContext) -> dict:
        """Update the RAG configuration for the agent."""
        try:
            # Get current config
            current_config = agent.rag_config or {}

            # Update with provided values
            if "enabled" in args:
                current_config["enabled"] = args["enabled"]
            if "top_k" in args:
                current_config["top_k"] = args["top_k"]
            if "similarity_threshold" in args:
                current_config["similarity_threshold"] = args["similarity_threshold"]
            if "chunk_size" in args:
                current_config["chunk_size"] = args["chunk_size"]
            if "chunk_overlap" in args:
                current_config["chunk_overlap"] = args["chunk_overlap"]

            # Save
            agent.rag_config = current_config
            await sync_to_async(agent.save)(update_fields=["rag_config"])
            await create_revision(agent, comment="Updated RAG configuration")

            return {
                "success": True,
                "message": "RAG configuration updated",
                "config": current_config,
            }
        except Exception as e:
            logger.exception("Error updating RAG config")
            return {"error": str(e)}

    async def _update_file_config(self, agent, args: dict, ctx: RunContext) -> dict:
        """Update the file upload and processing configuration for the agent."""
        try:
            # Get current config with defaults
            current_config = agent.file_config or {
                "enabled": False,
                "max_file_size_mb": 100,
                "allowed_types": ["image/*", "application/pdf", "text/*"],
                "ocr_provider": None,
                "vision_provider": None,
                "enable_thumbnails": True,
            }

            # Update with provided values
            if "enabled" in args:
                current_config["enabled"] = args["enabled"]
            if "max_file_size_mb" in args:
                current_config["max_file_size_mb"] = args["max_file_size_mb"]
            if "allowed_types" in args:
                current_config["allowed_types"] = args["allowed_types"]
            if "ocr_provider" in args:
                current_config["ocr_provider"] = args["ocr_provider"]
            if "vision_provider" in args:
                current_config["vision_provider"] = args["vision_provider"]
            if "enable_thumbnails" in args:
                current_config["enable_thumbnails"] = args["enable_thumbnails"]

            # Save
            agent.file_config = current_config
            await sync_to_async(agent.save)(update_fields=["file_config"])
            await create_revision(agent, comment="Updated file upload configuration")

            return {
                "success": True,
                "message": "File upload configuration updated",
                "config": current_config,
            }
        except Exception as e:
            logger.exception("Error updating file config")
            return {"error": str(e)}

    # ==========================================================================
    # Multi-Agent / Sub-Agent Tools
    # ==========================================================================

    async def _list_available_agents(self, current_agent, args: dict, ctx: RunContext) -> dict:
        """List all agents that can be used as sub-agents."""
        include_inactive = args.get("include_inactive", False)
        search = args.get("search", "")

        try:
            # Get all agents except the current one (can't be sub-agent of itself)
            query = AgentDefinition.objects.exclude(id=current_agent.id)

            if not include_inactive:
                query = query.filter(is_active=True)

            if search:
                from django.db.models import Q
                query = query.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(slug__icontains=search)
                )

            agents = await sync_to_async(list)(query.order_by("name")[:50])

            results = []
            for agent in agents:
                results.append({
                    "slug": agent.slug,
                    "name": agent.name,
                    "description": agent.description or "",
                    "is_active": agent.is_active,
                })

            return {
                "agents": results,
                "total": len(results),
                "message": f"Found {len(results)} available agents",
            }
        except Exception as e:
            logger.exception("Error listing available agents")
            return {"error": str(e)}

    async def _add_sub_agent_tool(self, agent, args: dict, ctx: RunContext) -> dict:
        """Add a sub-agent tool to the agent."""
        from django_agent_runtime.models import SubAgentTool
        from django_agent_studio.services.permissions import get_permission_service

        sub_agent_slug = args.get("sub_agent_slug")
        tool_name = args.get("tool_name")
        description = args.get("description")
        context_mode = args.get("context_mode", "message_only")

        if not all([sub_agent_slug, tool_name, description]):
            return {"error": "sub_agent_slug, tool_name, and description are required"}

        # Check permissions
        user = ctx.metadata.get("user")
        if user:
            permission_service = get_permission_service()
            if not permission_service.can_create_tool(user, agent):
                return {
                    "error": "Permission denied: You need CREATOR or ADMIN access level to add sub-agent tools.",
                    "hint": "Contact an administrator to request elevated permissions.",
                    "current_level": permission_service.get_user_access_level(user, agent),
                }

        try:
            # Find the sub-agent
            sub_agent = await sync_to_async(AgentDefinition.objects.get)(slug=sub_agent_slug)

            # Check for circular reference
            if sub_agent.id == agent.id:
                return {"error": "An agent cannot be a sub-agent of itself"}

            # Check if tool name already exists
            existing = await sync_to_async(
                SubAgentTool.objects.filter(parent_agent=agent, name=tool_name).exists
            )()
            if existing:
                return {
                    "error": f"A sub-agent tool named '{tool_name}' already exists",
                    "hint": "Use a different name or remove the existing tool first",
                }

            # Create the sub-agent tool
            sub_agent_tool = await sync_to_async(SubAgentTool.objects.create)(
                parent_agent=agent,
                sub_agent=sub_agent,
                name=tool_name,
                description=description,
                context_mode=context_mode,
            )

            # Create revision
            await create_revision(agent, comment=f"Added sub-agent tool: {tool_name} -> {sub_agent.name}")

            return {
                "success": True,
                "message": f"Added sub-agent tool '{tool_name}' pointing to '{sub_agent.name}'",
                "tool_id": str(sub_agent_tool.id),
                "tool_name": tool_name,
                "sub_agent_slug": sub_agent_slug,
                "context_mode": context_mode,
            }

        except AgentDefinition.DoesNotExist:
            return {
                "error": f"Sub-agent '{sub_agent_slug}' not found",
                "hint": "Use list_available_agents to see available agents",
            }
        except Exception as e:
            logger.exception("Error adding sub-agent tool")
            return {"error": str(e)}

    async def _list_sub_agent_tools(self, agent, args: dict, ctx: RunContext) -> dict:
        """List all sub-agent tools for the agent."""
        from django_agent_runtime.models import SubAgentTool

        try:
            tools = await sync_to_async(list)(
                agent.sub_agent_tools.select_related("sub_agent").all()
            )

            results = []
            for tool in tools:
                results.append({
                    "id": str(tool.id),
                    "name": tool.name,
                    "description": tool.description,
                    "sub_agent_slug": tool.sub_agent.slug,
                    "sub_agent_name": tool.sub_agent.name,
                    "context_mode": tool.context_mode,
                    "is_active": tool.is_active,
                })

            return {
                "sub_agent_tools": results,
                "total": len(results),
            }
        except Exception as e:
            logger.exception("Error listing sub-agent tools")
            return {"error": str(e)}

    async def _remove_sub_agent_tool(self, agent, args: dict, ctx: RunContext) -> dict:
        """Remove a sub-agent tool from the agent."""
        from django_agent_runtime.models import SubAgentTool
        from django_agent_studio.services.permissions import get_permission_service

        tool_name = args.get("tool_name")
        if not tool_name:
            return {"error": "tool_name is required"}

        # Check permissions
        user = ctx.metadata.get("user")
        if user:
            permission_service = get_permission_service()
            if not permission_service.can_create_tool(user, agent):
                return {
                    "error": "Permission denied: You need CREATOR or ADMIN access level to remove sub-agent tools.",
                    "hint": "Contact an administrator to request elevated permissions.",
                    "current_level": permission_service.get_user_access_level(user, agent),
                }

        try:
            tool = await sync_to_async(
                agent.sub_agent_tools.filter(name=tool_name).first
            )()

            if not tool:
                return {
                    "error": f"Sub-agent tool '{tool_name}' not found",
                    "hint": "Use list_sub_agent_tools to see existing tools",
                }

            sub_agent_name = await sync_to_async(lambda: tool.sub_agent.name)()
            await sync_to_async(tool.delete)()

            # Create revision
            await create_revision(agent, comment=f"Removed sub-agent tool: {tool_name}")

            return {
                "success": True,
                "message": f"Removed sub-agent tool '{tool_name}' (was pointing to '{sub_agent_name}')",
            }
        except Exception as e:
            logger.exception("Error removing sub-agent tool")
            return {"error": str(e)}

    async def _update_sub_agent_tool(self, agent, args: dict, ctx: RunContext) -> dict:
        """Update a sub-agent tool's configuration."""
        from django_agent_runtime.models import SubAgentTool
        from django_agent_studio.services.permissions import get_permission_service

        tool_name = args.get("tool_name")
        if not tool_name:
            return {"error": "tool_name is required"}

        # Check permissions
        user = ctx.metadata.get("user")
        if user:
            permission_service = get_permission_service()
            if not permission_service.can_create_tool(user, agent):
                return {
                    "error": "Permission denied: You need CREATOR or ADMIN access level to update sub-agent tools.",
                    "hint": "Contact an administrator to request elevated permissions.",
                    "current_level": permission_service.get_user_access_level(user, agent),
                }

        try:
            tool = await sync_to_async(
                agent.sub_agent_tools.filter(name=tool_name).first
            )()

            if not tool:
                return {
                    "error": f"Sub-agent tool '{tool_name}' not found",
                    "hint": "Use list_sub_agent_tools to see existing tools",
                }

            changes = []
            if "description" in args:
                tool.description = args["description"]
                changes.append("description")
            if "context_mode" in args:
                tool.context_mode = args["context_mode"]
                changes.append(f"context_mode={args['context_mode']}")

            if not changes:
                return {"error": "No changes specified. Provide description or context_mode."}

            await sync_to_async(tool.save)()

            # Create revision
            await create_revision(agent, comment=f"Updated sub-agent tool {tool_name}: {', '.join(changes)}")

            return {
                "success": True,
                "message": f"Updated sub-agent tool '{tool_name}'",
                "changes": changes,
            }
        except Exception as e:
            logger.exception("Error updating sub-agent tool")
            return {"error": str(e)}

    # ==========================================================================
    # UI Control Tools - Allow builder to switch agents/systems in the UI
    # ==========================================================================

    async def _switch_to_agent(self, args: dict, ctx: RunContext) -> dict:
        """Switch the UI to edit a different agent."""
        agent_slug = args.get("agent_slug")
        agent_id = args.get("agent_id")

        if not agent_slug and not agent_id:
            return {"error": "Either agent_slug or agent_id must be provided"}

        try:
            if agent_id:
                agent = await sync_to_async(AgentDefinition.objects.get)(id=agent_id)
            else:
                agent = await sync_to_async(AgentDefinition.objects.get)(slug=agent_slug)

            # Emit a special UI control event that the frontend can listen for
            await ctx.emit("ui.control", {
                "type": "ui_control",
                "action": "switch_agent",
                "agent_id": str(agent.id),
                "agent_slug": agent.slug,
                "agent_name": agent.name,
            })

            return {
                "success": True,
                "message": f"Switched to agent '{agent.name}' ({agent.slug})",
                "agent_id": str(agent.id),
                "agent_slug": agent.slug,
                "agent_name": agent.name,
            }
        except AgentDefinition.DoesNotExist:
            return {"error": f"Agent not found: {agent_slug or agent_id}"}
        except Exception as e:
            logger.exception("Error switching agent")
            return {"error": str(e)}

    async def _switch_to_system(self, args: dict, ctx: RunContext) -> dict:
        """Switch the UI to work with a multi-agent system."""
        from django_agent_runtime.models import AgentSystem

        system_slug = args.get("system_slug")
        system_id = args.get("system_id")

        if not system_slug and not system_id:
            return {"error": "Either system_slug or system_id must be provided"}

        try:
            if system_id:
                system = await sync_to_async(AgentSystem.objects.get)(id=system_id)
            else:
                system = await sync_to_async(AgentSystem.objects.get)(slug=system_slug)

            # Emit a special UI control event
            await ctx.emit("ui.control", {
                "type": "ui_control",
                "action": "switch_system",
                "system_id": str(system.id),
                "system_slug": system.slug,
                "system_name": system.name,
            })

            return {
                "success": True,
                "message": f"Switched to system '{system.name}' ({system.slug})",
                "system_id": str(system.id),
                "system_slug": system.slug,
                "system_name": system.name,
            }
        except AgentSystem.DoesNotExist:
            return {"error": f"System not found: {system_slug or system_id}"}
        except Exception as e:
            logger.exception("Error switching system")
            return {"error": str(e)}

    async def _list_all_agents(self, args: dict, ctx: RunContext) -> dict:
        """List all available agents in the system."""
        include_inactive = args.get("include_inactive", False)
        search = args.get("search", "")

        try:
            query = AgentDefinition.objects.all()
            if not include_inactive:
                query = query.filter(is_active=True)
            if search:
                query = query.filter(name__icontains=search) | query.filter(description__icontains=search)

            agents = await sync_to_async(list)(query.order_by("name")[:50])

            result = []
            for agent in agents:
                result.append({
                    "id": str(agent.id),
                    "slug": agent.slug,
                    "name": agent.name,
                    "description": agent.description or "",
                    "is_active": agent.is_active,
                    "icon": agent.icon or "🤖",
                })

            return {
                "agents": result,
                "total": len(result),
            }
        except Exception as e:
            logger.exception("Error listing agents")
            return {"error": str(e)}

    async def _list_all_systems(self, args: dict, ctx: RunContext) -> dict:
        """List all available multi-agent systems."""
        from django_agent_runtime.models import AgentSystem

        include_inactive = args.get("include_inactive", False)
        search = args.get("search", "")

        try:
            query = AgentSystem.objects.all()
            if not include_inactive:
                query = query.filter(is_active=True)
            if search:
                query = query.filter(name__icontains=search) | query.filter(description__icontains=search)

            systems = await sync_to_async(list)(query.order_by("name")[:50])

            result = []
            for system in systems:
                member_count = await sync_to_async(system.members.count)()
                entry_agent = await sync_to_async(lambda: system.entry_agent)()
                result.append({
                    "id": str(system.id),
                    "slug": system.slug,
                    "name": system.name,
                    "description": system.description or "",
                    "is_active": system.is_active,
                    "member_count": member_count,
                    "entry_agent_slug": entry_agent.slug if entry_agent else None,
                })

            return {
                "systems": result,
                "total": len(result),
            }
        except Exception as e:
            logger.exception("Error listing systems")
            return {"error": str(e)}

    async def _get_system_details(self, args: dict, ctx: RunContext) -> dict:
        """Get detailed information about a multi-agent system."""
        from django_agent_runtime.models import AgentSystem

        system_slug = args.get("system_slug")
        system_id = args.get("system_id")

        if not system_slug and not system_id:
            return {"error": "Either system_slug or system_id must be provided"}

        try:
            if system_id:
                system = await sync_to_async(AgentSystem.objects.get)(id=system_id)
            else:
                system = await sync_to_async(AgentSystem.objects.get)(slug=system_slug)

            # Get members
            members = await sync_to_async(list)(system.members.select_related("agent").all())
            member_list = []
            for member in members:
                agent = await sync_to_async(lambda m=member: m.agent)()
                member_list.append({
                    "id": str(member.id),
                    "agent_id": str(agent.id),
                    "agent_slug": agent.slug,
                    "agent_name": agent.name,
                    "role": member.role or "",
                    "is_entry_point": member.is_entry_point,
                })

            # Get entry agent
            entry_agent = await sync_to_async(lambda: system.entry_agent)()

            return {
                "id": str(system.id),
                "slug": system.slug,
                "name": system.name,
                "description": system.description or "",
                "is_active": system.is_active,
                "entry_agent": {
                    "id": str(entry_agent.id),
                    "slug": entry_agent.slug,
                    "name": entry_agent.name,
                } if entry_agent else None,
                "members": member_list,
                "member_count": len(member_list),
            }
        except AgentSystem.DoesNotExist:
            return {"error": f"System not found: {system_slug or system_id}"}
        except Exception as e:
            logger.exception("Error getting system details")
            return {"error": str(e)}

    # ==================== System Management Methods ====================

    async def _create_system(self, args: dict, ctx: RunContext) -> dict:
        """Create a new multi-agent system."""
        from django_agent_runtime.models import AgentSystem
        from django_agent_runtime.services.multi_agent import create_system_from_entry_agent

        name = args.get("name")
        entry_agent_slug = args.get("entry_agent_slug")

        if not name or not entry_agent_slug:
            return {"error": "name and entry_agent_slug are required"}

        # Generate slug if not provided
        slug = args.get("slug")
        if not slug:
            slug = slugify(name)

        description = args.get("description", "")
        auto_discover = args.get("auto_discover", True)

        try:
            # Check if slug already exists
            if await sync_to_async(AgentSystem.objects.filter(slug=slug).exists)():
                return {"error": f"System with slug '{slug}' already exists"}

            # Get the entry agent
            try:
                entry_agent = await sync_to_async(AgentDefinition.objects.get)(slug=entry_agent_slug)
            except AgentDefinition.DoesNotExist:
                return {"error": f"Entry agent not found: {entry_agent_slug}"}

            # Get owner from context if available
            owner = getattr(ctx, 'user', None)

            # Create the system
            system = await sync_to_async(create_system_from_entry_agent)(
                slug=slug,
                name=name,
                entry_agent=entry_agent,
                description=description,
                owner=owner,
                auto_discover=auto_discover,
            )

            # Get member count
            member_count = await sync_to_async(system.members.count)()

            return {
                "success": True,
                "message": f"Created system '{name}' with {member_count} member(s)",
                "system_id": str(system.id),
                "system_slug": system.slug,
                "member_count": member_count,
                "entry_agent_slug": entry_agent.slug,
            }
        except Exception as e:
            logger.exception("Error creating system")
            return {"error": str(e)}

    async def _add_agent_to_system(self, args: dict, ctx: RunContext) -> dict:
        """Add an agent to a multi-agent system."""
        from django_agent_runtime.models import AgentSystem, AgentSystemMember
        from django_agent_runtime.services.multi_agent import add_agent_to_system

        system_slug = args.get("system_slug")
        agent_slug = args.get("agent_slug")

        if not system_slug or not agent_slug:
            return {"error": "system_slug and agent_slug are required"}

        role = args.get("role", "specialist")
        notes = args.get("notes", "")

        try:
            # Get the system
            try:
                system = await sync_to_async(AgentSystem.objects.get)(slug=system_slug)
            except AgentSystem.DoesNotExist:
                return {"error": f"System not found: {system_slug}"}

            # Get the agent
            try:
                agent = await sync_to_async(AgentDefinition.objects.get)(slug=agent_slug)
            except AgentDefinition.DoesNotExist:
                return {"error": f"Agent not found: {agent_slug}"}

            # Check if agent is already a member
            existing = await sync_to_async(
                system.members.filter(agent=agent).exists
            )()
            if existing:
                return {"error": f"Agent '{agent_slug}' is already a member of system '{system_slug}'"}

            # Map role string to enum
            role_map = {
                "specialist": AgentSystemMember.Role.SPECIALIST,
                "utility": AgentSystemMember.Role.UTILITY,
                "supervisor": AgentSystemMember.Role.SUPERVISOR,
                "entry_point": AgentSystemMember.Role.ENTRY_POINT,
            }
            role_enum = role_map.get(role, AgentSystemMember.Role.SPECIALIST)

            # Add the agent
            member = await sync_to_async(add_agent_to_system)(
                system=system,
                agent=agent,
                role=role_enum,
                notes=notes,
            )

            return {
                "success": True,
                "message": f"Added agent '{agent_slug}' to system '{system_slug}' as {role}",
                "member_id": str(member.id),
                "agent_slug": agent_slug,
                "role": role,
            }
        except Exception as e:
            logger.exception("Error adding agent to system")
            return {"error": str(e)}

    async def _remove_agent_from_system(self, args: dict, ctx: RunContext) -> dict:
        """Remove an agent from a multi-agent system."""
        from django_agent_runtime.models import AgentSystem

        system_slug = args.get("system_slug")
        agent_slug = args.get("agent_slug")

        if not system_slug or not agent_slug:
            return {"error": "system_slug and agent_slug are required"}

        try:
            # Get the system
            try:
                system = await sync_to_async(AgentSystem.objects.get)(slug=system_slug)
            except AgentSystem.DoesNotExist:
                return {"error": f"System not found: {system_slug}"}

            # Get the agent
            try:
                agent = await sync_to_async(AgentDefinition.objects.get)(slug=agent_slug)
            except AgentDefinition.DoesNotExist:
                return {"error": f"Agent not found: {agent_slug}"}

            # Check if this is the entry agent
            entry_agent = await sync_to_async(lambda: system.entry_agent)()
            if entry_agent and entry_agent.slug == agent_slug:
                return {"error": f"Cannot remove entry agent '{agent_slug}'. Change the entry agent first."}

            # Find and delete the membership
            member = await sync_to_async(
                system.members.filter(agent=agent).first
            )()
            if not member:
                return {"error": f"Agent '{agent_slug}' is not a member of system '{system_slug}'"}

            await sync_to_async(member.delete)()

            return {
                "success": True,
                "message": f"Removed agent '{agent_slug}' from system '{system_slug}'",
            }
        except Exception as e:
            logger.exception("Error removing agent from system")
            return {"error": str(e)}

    async def _update_system_config(self, args: dict, ctx: RunContext) -> dict:
        """Update a multi-agent system's configuration."""
        from django_agent_runtime.models import AgentSystem

        system_slug = args.get("system_slug")
        if not system_slug:
            return {"error": "system_slug is required"}

        try:
            # Get the system
            try:
                system = await sync_to_async(AgentSystem.objects.get)(slug=system_slug)
            except AgentSystem.DoesNotExist:
                return {"error": f"System not found: {system_slug}"}

            changes = []

            # Update name
            if "name" in args:
                system.name = args["name"]
                changes.append(f"name='{args['name']}'")

            # Update description
            if "description" in args:
                system.description = args["description"]
                changes.append("description updated")

            # Update is_active
            if "is_active" in args:
                system.is_active = args["is_active"]
                changes.append(f"is_active={args['is_active']}")

            # Update entry agent
            if "entry_agent_slug" in args:
                new_entry_slug = args["entry_agent_slug"]
                try:
                    new_entry = await sync_to_async(AgentDefinition.objects.get)(slug=new_entry_slug)
                except AgentDefinition.DoesNotExist:
                    return {"error": f"Entry agent not found: {new_entry_slug}"}

                # Verify the new entry agent is a member
                is_member = await sync_to_async(
                    system.members.filter(agent=new_entry).exists
                )()
                if not is_member:
                    return {"error": f"Agent '{new_entry_slug}' must be a member of the system before becoming entry agent"}

                system.entry_agent = new_entry
                changes.append(f"entry_agent='{new_entry_slug}'")

            # Update shared knowledge
            if "shared_knowledge" in args:
                system.shared_knowledge = args["shared_knowledge"]
                changes.append(f"shared_knowledge ({len(args['shared_knowledge'])} items)")

            if not changes:
                return {"message": "No changes specified"}

            await sync_to_async(system.save)()

            return {
                "success": True,
                "message": f"Updated system '{system_slug}': {', '.join(changes)}",
                "changes": changes,
            }
        except Exception as e:
            logger.exception("Error updating system config")
            return {"error": str(e)}

    async def _delete_system(self, args: dict, ctx: RunContext) -> dict:
        """Delete a multi-agent system."""
        from django_agent_runtime.models import AgentSystem

        system_slug = args.get("system_slug")
        confirm = args.get("confirm", False)

        if not system_slug:
            return {"error": "system_slug is required"}

        if not confirm:
            return {"error": "Must set confirm=true to delete a system"}

        try:
            # Get the system
            try:
                system = await sync_to_async(AgentSystem.objects.get)(slug=system_slug)
            except AgentSystem.DoesNotExist:
                return {"error": f"System not found: {system_slug}"}

            system_name = system.name
            member_count = await sync_to_async(system.members.count)()

            # Delete the system (cascades to members, versions, snapshots)
            await sync_to_async(system.delete)()

            return {
                "success": True,
                "message": f"Deleted system '{system_name}' ({system_slug}) with {member_count} member(s). Agents were NOT deleted.",
            }
        except Exception as e:
            logger.exception("Error deleting system")
            return {"error": str(e)}

    # ==================== Spec Document Methods ====================

    async def _list_spec_documents(self, agent, args: dict, ctx: RunContext) -> dict:
        """List spec documents with optional filtering."""
        from django_agent_runtime.models import SpecDocument

        try:
            root_only = args.get("root_only", False)
            linked_only = args.get("linked_only", False)

            if root_only:
                docs = await sync_to_async(list)(
                    SpecDocument.objects.filter(parent__isnull=True)
                    .select_related("linked_agent")
                    .order_by("order", "title")
                )
            else:
                docs = await sync_to_async(list)(
                    SpecDocument.objects.all()
                    .select_related("linked_agent", "parent")
                    .order_by("parent_id", "order", "title")
                )

            if linked_only:
                docs = [d for d in docs if d.linked_agent_id]

            def format_doc(doc):
                result = {
                    "id": str(doc.id),
                    "title": doc.title,
                    "parent_id": str(doc.parent_id) if doc.parent_id else None,
                    "order": doc.order,
                    "current_version": doc.current_version,
                    "has_content": bool(doc.content),
                    "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content,
                }
                if doc.linked_agent:
                    result["linked_agent"] = {
                        "id": str(doc.linked_agent.id),
                        "slug": doc.linked_agent.slug,
                        "name": doc.linked_agent.name,
                    }
                return result

            return {
                "documents": [format_doc(d) for d in docs],
                "count": len(docs),
            }
        except Exception as e:
            logger.exception("Error listing spec documents")
            return {"error": str(e)}

    async def _get_spec_document(self, agent, args: dict, ctx: RunContext) -> dict:
        """Get a spec document by ID."""
        from django_agent_runtime.models import SpecDocument

        try:
            doc_id = args["document_id"]
            include_children = args.get("include_children", False)
            render_markdown = args.get("render_as_markdown", False)

            doc = await sync_to_async(
                SpecDocument.objects.select_related("linked_agent", "parent").get
            )(id=doc_id)

            result = {
                "id": str(doc.id),
                "title": doc.title,
                "content": doc.content,
                "parent_id": str(doc.parent_id) if doc.parent_id else None,
                "order": doc.order,
                "current_version": doc.current_version,
                "full_path": await sync_to_async(doc.get_full_path)(),
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
            }

            if doc.linked_agent:
                result["linked_agent"] = {
                    "id": str(doc.linked_agent.id),
                    "slug": doc.linked_agent.slug,
                    "name": doc.linked_agent.name,
                }

            if include_children:
                descendants = await sync_to_async(doc.get_descendants)()
                result["children"] = [
                    {
                        "id": str(d.id),
                        "title": d.title,
                        "parent_id": str(d.parent_id) if d.parent_id else None,
                        "has_content": bool(d.content),
                        "linked_agent_slug": d.linked_agent.slug if d.linked_agent else None,
                    }
                    for d in descendants
                ]

            if render_markdown:
                result["rendered_markdown"] = await sync_to_async(doc.render_tree_as_markdown)()

            return result
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except Exception as e:
            logger.exception("Error getting spec document")
            return {"error": str(e)}

    async def _create_spec_document(self, agent, args: dict, ctx: RunContext) -> dict:
        """Create a new spec document."""
        from django_agent_runtime.models import SpecDocument, AgentDefinition

        try:
            title = args["title"]
            content = args.get("content", "")
            parent_id = args.get("parent_id")
            linked_agent_id = args.get("linked_agent_id")
            order = args.get("order", 0)

            # Get parent if specified
            parent = None
            if parent_id:
                parent = await sync_to_async(SpecDocument.objects.get)(id=parent_id)

            # Get linked agent if specified
            linked_agent = None
            if linked_agent_id:
                linked_agent = await sync_to_async(AgentDefinition.objects.get)(id=linked_agent_id)

            # Create document
            doc = await sync_to_async(SpecDocument.objects.create)(
                title=title,
                content=content,
                parent=parent,
                linked_agent=linked_agent,
                order=order,
                owner=ctx.user if ctx.user and ctx.user.is_authenticated else None,
            )

            return {
                "success": True,
                "message": f"Created spec document: {title}",
                "document_id": str(doc.id),
                "version": doc.current_version,
                "linked_agent": linked_agent.slug if linked_agent else None,
            }
        except SpecDocument.DoesNotExist:
            return {"error": f"Parent document not found: {parent_id}"}
        except AgentDefinition.DoesNotExist:
            return {"error": f"Agent not found: {linked_agent_id}"}
        except Exception as e:
            logger.exception("Error creating spec document")
            return {"error": str(e)}

    async def _update_spec_document(self, agent, args: dict, ctx: RunContext) -> dict:
        """Update a spec document."""
        from django_agent_runtime.models import SpecDocument

        try:
            doc_id = args["document_id"]
            doc = await sync_to_async(SpecDocument.objects.get)(id=doc_id)

            changes = []
            if "title" in args:
                doc.title = args["title"]
                changes.append("title")
            if "content" in args:
                doc.content = args["content"]
                changes.append("content")
            if "order" in args:
                doc.order = args["order"]
                changes.append("order")

            if changes:
                await sync_to_async(doc.save)()
                return {
                    "success": True,
                    "message": f"Updated spec document: {', '.join(changes)}",
                    "document_id": str(doc.id),
                    "new_version": doc.current_version,
                }
            else:
                return {"message": "No changes specified"}
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except Exception as e:
            logger.exception("Error updating spec document")
            return {"error": str(e)}

    async def _link_spec_to_agent(self, agent, args: dict, ctx: RunContext) -> dict:
        """Link a spec document to an agent."""
        from django_agent_runtime.models import SpecDocument, AgentDefinition

        try:
            doc_id = args["document_id"]
            agent_id = args["agent_id"]

            doc = await sync_to_async(SpecDocument.objects.get)(id=doc_id)

            # Handle 'current' as the agent being edited
            if agent_id == "current":
                target_agent = agent
            else:
                target_agent = await sync_to_async(AgentDefinition.objects.get)(id=agent_id)

            doc.linked_agent = target_agent
            await sync_to_async(doc.save)()

            return {
                "success": True,
                "message": f"Linked document '{doc.title}' to agent '{target_agent.name}'",
                "document_id": str(doc.id),
                "agent_id": str(target_agent.id),
                "agent_slug": target_agent.slug,
            }
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except AgentDefinition.DoesNotExist:
            return {"error": f"Agent not found: {args.get('agent_id')}"}
        except Exception as e:
            logger.exception("Error linking spec to agent")
            return {"error": str(e)}

    async def _unlink_spec_from_agent(self, agent, args: dict, ctx: RunContext) -> dict:
        """Unlink a spec document from its agent."""
        from django_agent_runtime.models import SpecDocument

        try:
            doc_id = args["document_id"]
            doc = await sync_to_async(
                SpecDocument.objects.select_related("linked_agent").get
            )(id=doc_id)

            if not doc.linked_agent:
                return {"message": "Document is not linked to any agent"}

            old_agent_name = doc.linked_agent.name
            doc.linked_agent = None
            await sync_to_async(doc.save)()

            return {
                "success": True,
                "message": f"Unlinked document '{doc.title}' from agent '{old_agent_name}'",
                "document_id": str(doc.id),
            }
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except Exception as e:
            logger.exception("Error unlinking spec from agent")
            return {"error": str(e)}

    async def _get_spec_document_history(self, agent, args: dict, ctx: RunContext) -> dict:
        """Get version history of a spec document."""
        from django_agent_runtime.models import SpecDocument, SpecDocumentVersion

        try:
            doc_id = args["document_id"]
            limit = args.get("limit", 10)

            doc = await sync_to_async(SpecDocument.objects.get)(id=doc_id)
            versions = await sync_to_async(list)(
                doc.versions.all()[:limit]
            )

            return {
                "document_id": str(doc.id),
                "document_title": doc.title,
                "current_version": doc.current_version,
                "versions": [
                    {
                        "version_number": v.version_number,
                        "title": v.title,
                        "content_preview": v.content[:100] + "..." if len(v.content) > 100 else v.content,
                        "created_at": v.created_at.isoformat(),
                        "change_summary": v.change_summary or "",
                    }
                    for v in versions
                ],
            }
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except Exception as e:
            logger.exception("Error getting spec document history")
            return {"error": str(e)}

    async def _restore_spec_document_version(self, agent, args: dict, ctx: RunContext) -> dict:
        """Restore a spec document to a previous version."""
        from django_agent_runtime.models import SpecDocument, SpecDocumentVersion

        try:
            doc_id = args["document_id"]
            version_number = args["version_number"]

            doc = await sync_to_async(SpecDocument.objects.get)(id=doc_id)
            version = await sync_to_async(doc.versions.get)(version_number=version_number)

            # Restore creates a new version
            await sync_to_async(version.restore)()

            # Refresh doc to get new version number
            await sync_to_async(doc.refresh_from_db)()

            return {
                "success": True,
                "message": f"Restored document to version {version_number}",
                "document_id": str(doc.id),
                "restored_from_version": version_number,
                "new_version": doc.current_version,
            }
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except SpecDocumentVersion.DoesNotExist:
            return {"error": f"Version not found: {args.get('version_number')}"}
        except Exception as e:
            logger.exception("Error restoring spec document version")
            return {"error": str(e)}

    async def _delete_spec_document(self, agent, args: dict, ctx: RunContext) -> dict:
        """Delete a spec document."""
        from django_agent_runtime.models import SpecDocument

        try:
            doc_id = args["document_id"]
            confirm = args.get("confirm", False)

            if not confirm:
                return {"error": "Must set confirm=true to delete a document"}

            doc = await sync_to_async(SpecDocument.objects.get)(id=doc_id)
            title = doc.title

            # Count children that will be deleted
            children_count = await sync_to_async(doc.children.count)()

            await sync_to_async(doc.delete)()

            return {
                "success": True,
                "message": f"Deleted document '{title}'" + (f" and {children_count} children" if children_count else ""),
                "deleted_children": children_count,
            }
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('document_id')}"}
        except Exception as e:
            logger.exception("Error deleting spec document")
            return {"error": str(e)}

    async def _render_full_spec(self, agent, args: dict, ctx: RunContext) -> dict:
        """Render all spec documents as a single markdown document."""
        from django_agent_runtime.models import SpecDocument

        try:
            root_id = args.get("root_document_id")

            if root_id:
                # Render from specific root
                doc = await sync_to_async(SpecDocument.objects.get)(id=root_id)
                markdown = await sync_to_async(doc.render_tree_as_markdown)()
                return {
                    "markdown": markdown,
                    "root_document": doc.title,
                }
            else:
                # Render all root documents
                roots = await sync_to_async(list)(
                    SpecDocument.objects.filter(parent__isnull=True).order_by("order", "title")
                )

                parts = []
                for root in roots:
                    parts.append(await sync_to_async(root.render_tree_as_markdown)())

                return {
                    "markdown": "\n\n---\n\n".join(parts),
                    "root_count": len(roots),
                    "roots": [{"id": str(r.id), "title": r.title} for r in roots],
                }
        except SpecDocument.DoesNotExist:
            return {"error": f"Document not found: {args.get('root_document_id')}"}
        except Exception as e:
            logger.exception("Error rendering full spec")
            return {"error": str(e)}
