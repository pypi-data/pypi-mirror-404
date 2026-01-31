# Django Agent Studio

A visual agent builder and management interface for Django applications. Create, customize, and test AI agents through a conversational interface or REST API.

## Recent Updates

| Version | Date | Changes |
|---------|------|---------|
| **0.3.3** | 2026-01-30 | **Logout & Scroll Fixes** - Added logout button to header, fixed embedded chat widget scrolling with proper flex layout |
| **0.3.2** | 2026-01-30 | **Multi-User Access Control** - Collaborator management UI, user search autocomplete, supports both email and username-based User models, system creation from homepage, permission inheritance display |
| **0.3.1** | 2026-01-30 | **Bug Fixes** - Fixed duplicate message emit in dynamic agents, fixed escapejs encoding in templates, added 800px max-width constraint to system test view |
| **0.3.0** | 2026-01-29 | **System Listing & Navigation** - Browse and test multi-agent systems from homepage, fixed URL routing for My Systems/My Agents links, system creation now supports optional entry agent |
| **0.2.0** | 2026-01-28 | **Multi-Agent Systems** - System management UI, shared memory configuration, memory privacy controls, builder tools for managing agent systems |
| **0.1.9** | 2026-01-27 | Spec documents migration, improved builder agent |
| **0.1.0** | 2026-01-25 | Initial release with builder interface, dynamic tools, knowledge management |

## Features

### 🤖 Agent Builder Interface

A two-pane interface for building agents:
- **Left pane**: Test your agent in real-time
- **Right pane**: Conversational builder agent that helps you configure your agent

The builder agent can:
- Create new agents
- Update system prompts, models, and settings
- Add/remove tools and knowledge sources
- Scan your Django project for functions to use as tools
- Manage RAG (Retrieval-Augmented Generation) configuration

### 🔧 Dynamic Tool Discovery

Automatically discover functions in your Django project that can be used as agent tools:

```python
# Functions like this are automatically discovered
def get_customer_orders(customer_id: int, limit: int = 10) -> list[dict]:
    """
    Fetch recent orders for a customer.
    
    Args:
        customer_id: The customer's ID
        limit: Maximum number of orders to return
    
    Returns:
        List of order dictionaries
    """
    return Order.objects.filter(customer_id=customer_id)[:limit]
```

The scanner extracts:
- Function signatures and parameters
- Type hints and docstrings
- Whether functions are async
- Side effect detection (writes, deletes, etc.)

### 📚 Knowledge Management

Add context to your agents through multiple knowledge types:
- **Text**: Direct text content
- **URL**: Web pages (fetched and indexed)
- **File**: Uploaded documents
- **Dynamic**: Generated at runtime via callbacks

Knowledge can be:
- Always included in context
- Included via RAG similarity search
- Included on-demand when relevant

### 🔐 Permission System

Fine-grained access control for dynamic tool operations:

| Level | Capabilities |
|-------|-------------|
| **None** | No access to dynamic tools |
| **Viewer** | View discovered functions and existing tools |
| **Scanner** | Scan project for functions |
| **Requester** | Request tool creation (needs admin approval) |
| **Creator** | Create tools directly |
| **Admin** | Full access including approving requests |

### ✅ Approval Workflow

For organizations requiring oversight:
1. Users with "Requester" access submit tool creation requests
2. Admins review proposed tool configurations
3. Admins can approve (with optional modifications) or reject
4. Approved tools are automatically created and marked as verified

### 📝 Version Control

- **Agent Versions**: Create and manage multiple versions of an agent
- **Revisions**: Automatic snapshots after every change
- **Restore**: Roll back to any previous revision

## Installation

```bash
pip install django-agent-studio
```

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'django_agent_runtime',  # Required dependency
    'django_agent_studio',
]
```

Include the URLs:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('studio/', include('django_agent_studio.urls')),
    path('api/agent-runtime/', include('django_agent_runtime.api.urls')),
]
```

Run migrations:

```bash
python manage.py migrate
```

## Usage

### Web Interface

Navigate to `/studio/` to access the agent builder interface.

### REST API

#### Agents

```http
# List your agents
GET /studio/api/agents/

# Create an agent
POST /studio/api/agents/
{
    "name": "Customer Support Bot",
    "description": "Helps customers with orders and returns"
}

# Get agent details
GET /studio/api/agents/{id}/

# Get full agent schema (for debugging/export)
GET /studio/api/agents/{id}/full-schema/

# Update agent schema
PUT /studio/api/agents/{id}/full-schema/
```

#### Versions

```http
# List versions
GET /studio/api/agents/{id}/versions/

# Create a new version
POST /studio/api/agents/{id}/versions/

# Activate a version
POST /studio/api/agents/{id}/versions/{version_id}/activate/
```

#### Tools

```http
# List agent tools
GET /studio/api/agents/{id}/tools/

# Add a tool
POST /studio/api/agents/{id}/tools/

# List dynamic tools
GET /studio/api/agents/{id}/dynamic-tools/

# Toggle dynamic tool active status
POST /studio/api/agents/{id}/dynamic-tools/{tool_id}/toggle/
```

#### Knowledge

```http
# List knowledge sources
GET /studio/api/agents/{id}/knowledge/

# Add knowledge
POST /studio/api/agents/{id}/knowledge/
{
    "name": "Product FAQ",
    "knowledge_type": "text",
    "content": "Q: How do I return an item?...",
    "inclusion_mode": "always"
}
```

#### Dynamic Tool Discovery

```http
# Scan project for functions
POST /studio/api/agents/{id}/scan-project/
{
    "include_private": false,
    "include_tests": false,
    "app_filter": "myapp"
}

# List discovered functions
GET /studio/api/discovered-functions/

# Generate tools from functions
POST /studio/api/agents/{id}/generate-tools/
{
    "function_ids": ["uuid1", "uuid2"],
    "requires_confirmation": true
}
```

#### Approval Workflow

```http
# List approval requests
GET /studio/api/tool-approval-requests/

# Review a request (admin only)
POST /studio/api/tool-approval-requests/{id}/review/
{
    "action": "approve",  # or "reject"
    "review_notes": "Looks good!",
    "override_name": "custom_tool_name"  # optional
}

# Cancel your own request
POST /studio/api/tool-approval-requests/{id}/cancel/
```

#### Permission Management

```http
# Get your access level
GET /studio/api/dynamic-tool-access/me/

# Grant access (admin only)
POST /studio/api/dynamic-tool-access/grant/
{
    "user_id": 123,
    "access_level": "creator",
    "restricted_to_agent_ids": ["uuid1"],  # optional
    "notes": "Granted for project X"
}

# Revoke access (admin only)
POST /studio/api/dynamic-tool-access/revoke/
{
    "user_id": 123
}
```

#### Templates

```http
# List public template agents
GET /studio/api/templates/

# Fork a template
POST /studio/api/agents/{id}/fork/
```

## Builder Agent

The builder agent (`agent-builder`) is a special agent that helps users create and configure other agents through conversation. It has access to tools for:

- `create_agent` - Create a new agent
- `get_current_config` - View current agent configuration
- `update_system_prompt` - Update the agent's personality/instructions
- `update_agent_name` - Change name and description
- `update_model_settings` - Change LLM model and parameters
- `add_knowledge` - Add knowledge sources
- `remove_knowledge` - Remove knowledge sources
- `scan_project_for_tools` - Discover functions in the codebase
- `list_discovered_functions` - Browse discovered functions
- `get_function_details` - Get details about a specific function
- `add_tool_from_function` - Add a function as a tool
- `list_agent_tools` - List all tools on the agent
- `remove_tool` - Remove a tool
- `list_revisions` - View revision history
- `get_revision` - Get a specific revision
- `restore_revision` - Restore to a previous state
- `index_knowledge` - Index knowledge for RAG
- `get_rag_status` - Check RAG indexing status
- `preview_rag_search` - Test RAG search queries
- `update_rag_config` - Configure RAG settings

## Multi-Agent Systems

Django Agent Studio supports building multi-agent systems where agents can invoke other agents as tools. This enables powerful patterns like routers, specialists, and hierarchical agent teams.

### Overview

Multi-agent systems use the "agent-as-tool" pattern from `agent-runtime-core`:

- **Router Pattern**: A main agent routes requests to specialist agents
- **Delegation**: Sub-agents run and return results to the parent
- **Handoff**: Control transfers completely to a sub-agent

For full documentation, see:
- [agent-runtime-core Multi-Agent Systems](https://github.com/makemore/agent-runtime-core#multi-agent-systems)
- [django-agent-runtime Multi-Agent Systems](https://github.com/makemore/django-agent-runtime#multi-agent-systems)

### Using Multi-Agent with Studio Agents

Studio-created agents can be used as sub-agents in code-defined router agents:

```python
from django_agent_studio.runtime import StudioAgentRuntime
from agent_runtime_core.multi_agent import AgentTool, InvocationMode, ContextMode

# Load a studio-created agent
billing_agent = StudioAgentRuntime.from_agent_id("uuid-of-billing-agent")

# Wrap it as a tool
billing_tool = AgentTool(
    agent=billing_agent,
    name="billing_specialist",
    description="Handles billing questions and refunds",
    invocation_mode=InvocationMode.DELEGATE,
)

# Use in a router agent
class RouterAgent(AgentRuntime):
    def __init__(self):
        self.agent_tools = [billing_tool]

    async def run(self, ctx: RunContext) -> RunResult:
        # Register and use agent tools...
        pass
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **AgentTool** | Wraps any agent to be callable as a tool |
| **DELEGATE mode** | Sub-agent returns result to parent (parent continues) |
| **HANDOFF mode** | Control transfers to sub-agent (parent exits) |
| **Context modes** | FULL (all history), SUMMARY, or MESSAGE_ONLY |

### Events

Multi-agent invocations emit events for observability:

- `sub_agent.start` - Sub-agent invocation started
- `sub_agent.end` - Sub-agent completed
- Events include `parent_run_id` and `sub_agent_run_id` for tracing

## Configuration

Configure via Django settings or environment variables:

```python
AGENT_RUNTIME = {
    # Default model for new agents
    'DEFAULT_MODEL': 'gpt-4o',
    
    # RAG settings
    'RAG_EMBEDDING_MODEL': 'text-embedding-3-small',
    'RAG_CHUNK_SIZE': 500,
    'RAG_CHUNK_OVERLAP': 50,
}
```

## Dependencies

- `django-agent-runtime` - Core agent runtime
- `agent-runtime-core` - Agent execution framework
- `agent-frontend` - Chat widget for the UI

## License

MIT

