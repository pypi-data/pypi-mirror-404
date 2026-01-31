"""
API URL configuration for django_agent_studio.
"""

from django.urls import path

from django_agent_studio.api import views

urlpatterns = [
    # Agent definition CRUD
    path("agents/", views.AgentDefinitionListCreateView.as_view(), name="api_agent_list"),
    path("agents/<uuid:pk>/", views.AgentDefinitionDetailView.as_view(), name="api_agent_detail"),

    # Agent versions
    path(
        "agents/<uuid:agent_id>/versions/",
        views.AgentVersionListCreateView.as_view(),
        name="version_list",
    ),
    path(
        "agents/<uuid:agent_id>/versions/<uuid:pk>/",
        views.AgentVersionDetailView.as_view(),
        name="version_detail",
    ),
    path(
        "agents/<uuid:agent_id>/versions/<uuid:pk>/activate/",
        views.AgentVersionActivateView.as_view(),
        name="version_activate",
    ),

    # Agent tools
    path(
        "agents/<uuid:agent_id>/tools/",
        views.AgentToolListCreateView.as_view(),
        name="tool_list",
    ),
    path(
        "agents/<uuid:agent_id>/tools/<uuid:pk>/",
        views.AgentToolDetailView.as_view(),
        name="tool_detail",
    ),

    # Agent knowledge
    path(
        "agents/<uuid:agent_id>/knowledge/",
        views.AgentKnowledgeListCreateView.as_view(),
        name="knowledge_list",
    ),
    path(
        "agents/<uuid:agent_id>/knowledge/<uuid:pk>/",
        views.AgentKnowledgeDetailView.as_view(),
        name="knowledge_detail",
    ),

    # Template agents (public)
    path("templates/", views.TemplateAgentListView.as_view(), name="template_list"),

    # Fork an agent from template
    path("agents/<uuid:pk>/fork/", views.AgentForkView.as_view(), name="agent_fork"),

    # ==========================================================================
    # Dynamic Tool Discovery Endpoints
    # ==========================================================================

    # Scan project for functions
    path(
        "agents/<uuid:agent_id>/scan-project/",
        views.ProjectScanView.as_view(),
        name="scan_project",
    ),

    # Generate tools from discovered functions
    path(
        "agents/<uuid:agent_id>/generate-tools/",
        views.GenerateToolsView.as_view(),
        name="generate_tools",
    ),

    # List discovered functions
    path(
        "discovered-functions/",
        views.DiscoveredFunctionListView.as_view(),
        name="discovered_function_list",
    ),

    # Dynamic tools for an agent
    path(
        "agents/<uuid:agent_id>/dynamic-tools/",
        views.DynamicToolListView.as_view(),
        name="dynamic_tool_list",
    ),
    path(
        "agents/<uuid:agent_id>/dynamic-tools/<uuid:pk>/",
        views.DynamicToolDetailView.as_view(),
        name="dynamic_tool_detail",
    ),
    path(
        "agents/<uuid:agent_id>/dynamic-tools/<uuid:pk>/toggle/",
        views.DynamicToolToggleView.as_view(),
        name="dynamic_tool_toggle",
    ),

    # Dynamic tool executions (audit log)
    path(
        "agents/<uuid:agent_id>/dynamic-tools/<uuid:tool_id>/executions/",
        views.DynamicToolExecutionListView.as_view(),
        name="dynamic_tool_executions",
    ),

    # ==========================================================================
    # Approval Workflow Endpoints
    # ==========================================================================

    # List approval requests
    path(
        "tool-approval-requests/",
        views.ToolApprovalRequestListView.as_view(),
        name="approval_request_list",
    ),
    path(
        "tool-approval-requests/<uuid:pk>/",
        views.ToolApprovalRequestDetailView.as_view(),
        name="approval_request_detail",
    ),
    path(
        "tool-approval-requests/<uuid:pk>/review/",
        views.ToolApprovalReviewView.as_view(),
        name="approval_request_review",
    ),
    path(
        "tool-approval-requests/<uuid:pk>/cancel/",
        views.ToolApprovalCancelView.as_view(),
        name="approval_request_cancel",
    ),

    # ==========================================================================
    # Permission Management Endpoints
    # ==========================================================================

    # List/manage user access
    path(
        "dynamic-tool-access/",
        views.UserAccessListView.as_view(),
        name="user_access_list",
    ),
    path(
        "dynamic-tool-access/<uuid:pk>/",
        views.UserAccessDetailView.as_view(),
        name="user_access_detail",
    ),
    path(
        "dynamic-tool-access/grant/",
        views.GrantAccessView.as_view(),
        name="grant_access",
    ),
    path(
        "dynamic-tool-access/revoke/",
        views.RevokeAccessView.as_view(),
        name="revoke_access",
    ),
    path(
        "dynamic-tool-access/me/",
        views.MyAccessView.as_view(),
        name="my_access",
    ),

    # ==========================================================================
    # Model Selection Endpoints
    # ==========================================================================

    # List available models
    path(
        "models/",
        views.ModelsListView.as_view(),
        name="models_list",
    ),

    # ==========================================================================
    # Agent Schema Editor Endpoints
    # ==========================================================================

    # Full agent schema (for debugging/editing)
    path(
        "agents/<uuid:pk>/full-schema/",
        views.AgentFullSchemaView.as_view(),
        name="agent_full_schema",
    ),

    # ==========================================================================
    # Multi-Agent System Endpoints
    # ==========================================================================

    # List and create systems
    path(
        "systems/",
        views.AgentSystemListCreateView.as_view(),
        name="api_system_list",
    ),
    path(
        "systems/<uuid:pk>/",
        views.AgentSystemDetailView.as_view(),
        name="api_system_detail",
    ),

    # System members
    path(
        "systems/<uuid:system_id>/members/",
        views.AgentSystemMemberListCreateView.as_view(),
        name="api_system_member_list",
    ),
    path(
        "systems/<uuid:system_id>/members/<uuid:pk>/",
        views.AgentSystemMemberDetailView.as_view(),
        name="api_system_member_detail",
    ),

    # System versions
    path(
        "systems/<uuid:system_id>/versions/",
        views.AgentSystemVersionListView.as_view(),
        name="api_system_version_list",
    ),
    path(
        "systems/<uuid:system_id>/publish/",
        views.AgentSystemPublishView.as_view(),
        name="api_system_publish",
    ),
    path(
        "systems/<uuid:system_id>/versions/<uuid:version_id>/deploy/",
        views.AgentSystemDeployView.as_view(),
        name="api_system_deploy",
    ),
    path(
        "systems/<uuid:system_id>/versions/<uuid:version_id>/export/",
        views.AgentSystemExportView.as_view(),
        name="api_system_export",
    ),

    # Discover agents from entry point
    path(
        "agents/<uuid:agent_id>/discover-system/",
        views.AgentSystemDiscoverView.as_view(),
        name="discover_system",
    ),

    # ==========================================================================
    # Spec Document Endpoints
    # ==========================================================================

    # List and create spec documents
    path(
        "spec-documents/",
        views.SpecDocumentListCreateView.as_view(),
        name="spec_document_list",
    ),
    path(
        "spec-documents/<uuid:pk>/",
        views.SpecDocumentDetailView.as_view(),
        name="spec_document_detail",
    ),

    # Link/unlink to agent
    path(
        "spec-documents/<uuid:pk>/link/",
        views.SpecDocumentLinkView.as_view(),
        name="spec_document_link",
    ),

    # Version history
    path(
        "spec-documents/<uuid:pk>/history/",
        views.SpecDocumentHistoryView.as_view(),
        name="spec_document_history",
    ),

    # Restore version
    path(
        "spec-documents/<uuid:pk>/restore/",
        views.SpecDocumentRestoreView.as_view(),
        name="spec_document_restore",
    ),

    # Tree view
    path(
        "spec-documents/tree/",
        views.SpecDocumentTreeView.as_view(),
        name="spec_document_tree",
    ),

    # Render as markdown
    path(
        "spec-documents/render/",
        views.SpecDocumentRenderView.as_view(),
        name="spec_document_render",
    ),

    # Agent-specific spec document (get/update the spec linked to an agent)
    path(
        "agents/<uuid:agent_id>/spec/",
        views.AgentSpecDocumentView.as_view(),
        name="agent_spec_document",
    ),

    # ==========================================================================
    # Collaborator Management Endpoints
    # ==========================================================================

    # Agent collaborators
    path(
        "agents/<uuid:agent_id>/collaborators/",
        views.AgentCollaboratorListCreateView.as_view(),
        name="agent_collaborator_list",
    ),
    path(
        "agents/<uuid:agent_id>/collaborators/<uuid:pk>/",
        views.AgentCollaboratorDetailView.as_view(),
        name="agent_collaborator_detail",
    ),

    # System collaborators
    path(
        "systems/<uuid:system_id>/collaborators/",
        views.SystemCollaboratorListCreateView.as_view(),
        name="system_collaborator_list",
    ),
    path(
        "systems/<uuid:system_id>/collaborators/<uuid:pk>/",
        views.SystemCollaboratorDetailView.as_view(),
        name="system_collaborator_detail",
    ),

    # User search for collaborator autocomplete
    path(
        "users/search/",
        views.UserSearchView.as_view(),
        name="user_search",
    ),
]
