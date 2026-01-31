"""
Django app configuration for django_agent_studio.
"""

from django.apps import AppConfig


class DjangoAgentStudioConfig(AppConfig):
    """Configuration for the Django Agent Studio app."""

    name = "django_agent_studio"
    verbose_name = "Django Agent Studio"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """
        Called when Django starts. Used to:
        - Register the builder agent runtime
        - Set up signal handlers
        """
        from django_agent_studio.agents import register_studio_agents
        
        register_studio_agents()

