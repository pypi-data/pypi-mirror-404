"""
URL configuration for django_agent_studio.
"""

from django.urls import path, include

from django_agent_studio import views
from django_agent_studio.api import urls as api_urls

app_name = "agent_studio"

urlpatterns = [
    # Main studio interface
    path("", views.StudioHomeView.as_view(), name="home"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Systems (multi-agent systems)
    path("systems/", views.SystemListView.as_view(), name="system_list"),
    path("systems/create/", views.SystemCreateView.as_view(), name="system_create"),
    path("systems/<uuid:system_id>/test/", views.SystemTestView.as_view(), name="system_test"),
    path("systems/<uuid:system_id>/collaborators/", views.SystemCollaboratorsView.as_view(), name="system_collaborators"),

    # Agent builder/editor
    path("agents/", views.AgentListView.as_view(), name="agent_list"),
    path("agents/new/", views.AgentBuilderView.as_view(), name="agent_create"),
    path("agents/<uuid:agent_id>/", views.AgentBuilderView.as_view(), name="agent_edit"),
    path("agents/<uuid:agent_id>/test/", views.AgentTestView.as_view(), name="agent_test"),
    path("agents/<uuid:agent_id>/collaborators/", views.AgentCollaboratorsView.as_view(), name="agent_collaborators"),

    # API endpoints
    path("api/", include(api_urls)),
]

