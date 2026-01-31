"""
Agent implementations for django_agent_studio.

Provides:
- DynamicAgent: Loads configuration from AgentDefinition model
- BuilderAgent: The agent that helps users build/customize other agents
"""

from django_agent_studio.agents.dynamic import DynamicAgentRuntime
from django_agent_studio.agents.builder import BuilderAgentRuntime


def register_studio_agents():
    """Register the studio agents with the runtime registry."""
    from django_agent_runtime.runtime.registry import register_runtime
    
    # Register the builder agent
    register_runtime(BuilderAgentRuntime())
    
    # Note: DynamicAgentRuntime instances are registered on-demand
    # when an AgentDefinition is accessed


__all__ = [
    "DynamicAgentRuntime",
    "BuilderAgentRuntime",
    "register_studio_agents",
]

