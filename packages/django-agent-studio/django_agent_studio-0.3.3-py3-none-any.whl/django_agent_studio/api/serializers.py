"""
API serializers for django_agent_studio.
"""

from rest_framework import serializers

from django_agent_runtime.models import (
    AgentDefinition,
    AgentVersion,
    AgentTool,
    AgentKnowledge,
    DiscoveredFunction,
    DynamicTool,
    DynamicToolExecution,
    # Multi-agent system models
    AgentSystem,
    AgentSystemMember,
    AgentSystemVersion,
    AgentSystemSnapshot,
    # Collaborator models
    CollaboratorRole,
    AgentCollaborator,
    SystemCollaborator,
)


class AgentToolSerializer(serializers.ModelSerializer):
    """Serializer for AgentTool."""
    
    class Meta:
        model = AgentTool
        fields = [
            "id",
            "name",
            "tool_type",
            "description",
            "parameters_schema",
            "builtin_ref",
            "subagent",
            "config",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]


class AgentKnowledgeSerializer(serializers.ModelSerializer):
    """Serializer for AgentKnowledge."""
    
    class Meta:
        model = AgentKnowledge
        fields = [
            "id",
            "name",
            "knowledge_type",
            "content",
            "file",
            "url",
            "dynamic_config",
            "inclusion_mode",
            "is_active",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AgentVersionSerializer(serializers.ModelSerializer):
    """Serializer for AgentVersion."""
    
    class Meta:
        model = AgentVersion
        fields = [
            "id",
            "version",
            "system_prompt",
            "model",
            "model_settings",
            "extra_config",
            "is_active",
            "is_draft",
            "notes",
            "created_at",
            "published_at",
        ]
        read_only_fields = ["id", "created_at", "published_at"]


class AgentDefinitionListSerializer(serializers.ModelSerializer):
    """Serializer for listing AgentDefinitions."""

    active_version = serializers.SerializerMethodField()
    tools_count = serializers.SerializerMethodField()
    knowledge_count = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source='owner.email', read_only=True, allow_null=True)

    class Meta:
        model = AgentDefinition
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "icon",
            "parent",
            "owner",
            "owner_email",
            "is_public",
            "is_template",
            "is_active",
            "active_version",
            "tools_count",
            "knowledge_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "owner_email", "created_at", "updated_at"]

    def get_active_version(self, obj):
        version = obj.versions.filter(is_active=True).first()
        if version:
            return {"id": str(version.id), "version": version.version}
        return None

    def get_tools_count(self, obj):
        return obj.tools.filter(is_active=True).count()

    def get_knowledge_count(self, obj):
        return obj.knowledge_sources.filter(is_active=True).count()


class AgentDefinitionDetailSerializer(serializers.ModelSerializer):
    """Serializer for AgentDefinition detail view."""

    versions = AgentVersionSerializer(many=True, read_only=True)
    tools = AgentToolSerializer(many=True, read_only=True)
    knowledge_sources = AgentKnowledgeSerializer(many=True, read_only=True)
    effective_config = serializers.SerializerMethodField()
    owner_email = serializers.EmailField(source='owner.email', read_only=True, allow_null=True)

    class Meta:
        model = AgentDefinition
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "icon",
            "parent",
            "owner",
            "owner_email",
            "is_public",
            "is_template",
            "is_active",
            "versions",
            "tools",
            "knowledge_sources",
            "effective_config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "owner_email", "created_at", "updated_at", "effective_config"]

    def get_effective_config(self, obj):
        return obj.get_effective_config()


class DiscoveredFunctionSerializer(serializers.ModelSerializer):
    """Serializer for DiscoveredFunction."""

    class Meta:
        model = DiscoveredFunction
        fields = [
            "id",
            "name",
            "module_path",
            "function_path",
            "function_type",
            "class_name",
            "file_path",
            "line_number",
            "signature",
            "docstring",
            "parameters",
            "return_type",
            "is_async",
            "has_side_effects",
            "is_private",
            "is_selected",
            "scan_session",
            "discovered_at",
        ]
        read_only_fields = [
            "id", "discovered_at", "scan_session",
        ]


class DynamicToolSerializer(serializers.ModelSerializer):
    """Serializer for DynamicTool."""

    class Meta:
        model = DynamicTool
        fields = [
            "id",
            "name",
            "description",
            "function_path",
            "source_file",
            "source_line",
            "parameters_schema",
            "execution_mode",
            "timeout_seconds",
            "is_safe",
            "requires_confirmation",
            "allowed_for_auto_execution",
            "allowed_imports",
            "blocked_imports",
            "is_active",
            "is_verified",
            "version",
            "created_at",
            "updated_at",
            "discovered_function",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "version",
        ]


class DynamicToolExecutionSerializer(serializers.ModelSerializer):
    """Serializer for DynamicToolExecution."""

    tool_name = serializers.CharField(source='tool.name', read_only=True)

    class Meta:
        model = DynamicToolExecution
        fields = [
            "id",
            "tool",
            "tool_name",
            "agent_run_id",
            "input_arguments",
            "output_result",
            "error_message",
            "status",
            "started_at",
            "completed_at",
            "duration_ms",
            "was_sandboxed",
            "user_confirmed",
        ]
        read_only_fields = fields


class ProjectScanRequestSerializer(serializers.Serializer):
    """Serializer for project scan request."""

    directory = serializers.CharField(
        required=False,
        help_text="Specific directory to scan (relative to project root)",
    )
    include_private = serializers.BooleanField(
        default=False,
        help_text="Include private functions (starting with _)",
    )
    include_tests = serializers.BooleanField(
        default=False,
        help_text="Include test files",
    )
    app_filter = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of app names to scan",
    )


class GenerateToolsRequestSerializer(serializers.Serializer):
    """Serializer for tool generation request."""

    function_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of DiscoveredFunction IDs to convert to tools",
    )
    name_prefix = serializers.CharField(
        required=False,
        default="",
        help_text="Prefix to add to tool names",
    )
    requires_confirmation = serializers.BooleanField(
        default=True,
        help_text="Default value for requires_confirmation",
    )
    request_reason = serializers.CharField(
        required=False,
        default="",
        help_text="Reason for requesting these tools (for approval workflow)",
    )


# =============================================================================
# Approval Workflow Serializers
# =============================================================================

from django_agent_studio.models import (
    UserDynamicToolAccess,
    ToolApprovalRequest,
    DynamicToolAccessLevel,
)


class UserDynamicToolAccessSerializer(serializers.ModelSerializer):
    """Serializer for UserDynamicToolAccess."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    granted_by_email = serializers.EmailField(source='granted_by.email', read_only=True)
    access_level_display = serializers.CharField(
        source='get_access_level_display', read_only=True
    )

    class Meta:
        model = UserDynamicToolAccess
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "access_level",
            "access_level_display",
            "restricted_to_agents",
            "granted_by",
            "granted_by_email",
            "granted_at",
            "updated_at",
            "notes",
        ]
        read_only_fields = ["id", "granted_at", "updated_at", "granted_by"]


class ToolApprovalRequestSerializer(serializers.ModelSerializer):
    """Serializer for ToolApprovalRequest."""

    requester_email = serializers.EmailField(source='requester.email', read_only=True)
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    reviewed_by_email = serializers.EmailField(
        source='reviewed_by.email', read_only=True, allow_null=True
    )
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    function_path = serializers.CharField(
        source='discovered_function.function_path', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ToolApprovalRequest
        fields = [
            "id",
            "agent",
            "agent_name",
            "discovered_function",
            "function_path",
            "proposed_name",
            "proposed_description",
            "proposed_is_safe",
            "proposed_requires_confirmation",
            "proposed_timeout_seconds",
            "requester",
            "requester_email",
            "requester_name",
            "request_reason",
            "status",
            "status_display",
            "reviewed_by",
            "reviewed_by_email",
            "reviewed_at",
            "review_notes",
            "created_tool",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "requester", "status", "reviewed_by", "reviewed_at",
            "created_tool", "created_at", "updated_at",
        ]


class ToolApprovalReviewSerializer(serializers.Serializer):
    """Serializer for reviewing a tool approval request."""

    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        help_text="Action to take on the request",
    )
    review_notes = serializers.CharField(
        required=False,
        default="",
        help_text="Notes about the review decision",
    )
    # Allow overriding proposed values on approval
    override_name = serializers.CharField(required=False)
    override_description = serializers.CharField(required=False)
    override_is_safe = serializers.BooleanField(required=False)
    override_requires_confirmation = serializers.BooleanField(required=False)
    override_timeout_seconds = serializers.IntegerField(required=False, min_value=1)


class GrantAccessSerializer(serializers.Serializer):
    """Serializer for granting dynamic tool access to a user."""

    user_id = serializers.IntegerField(help_text="User ID to grant access to")
    access_level = serializers.ChoiceField(
        choices=DynamicToolAccessLevel.choices,
        help_text="Access level to grant",
    )
    restricted_to_agent_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Optional list of agent IDs to restrict access to",
    )
    notes = serializers.CharField(
        required=False,
        default="",
        help_text="Notes about why access was granted",
    )


# =============================================================================
# Multi-Agent System Serializers
# =============================================================================


class AgentSystemMemberSerializer(serializers.ModelSerializer):
    """Serializer for AgentSystemMember."""

    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_slug = serializers.CharField(source='agent.slug', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = AgentSystemMember
        fields = [
            "id",
            "agent",
            "agent_name",
            "agent_slug",
            "role",
            "role_display",
            "notes",
            "order",
        ]
        read_only_fields = ["id"]


class AgentSystemSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for AgentSystemSnapshot."""

    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_slug = serializers.CharField(source='agent.slug', read_only=True)
    revision_number = serializers.IntegerField(
        source='pinned_revision.revision_number', read_only=True
    )

    class Meta:
        model = AgentSystemSnapshot
        fields = [
            "id",
            "agent",
            "agent_name",
            "agent_slug",
            "pinned_revision",
            "revision_number",
            "tool_config_overrides",
        ]
        read_only_fields = ["id"]


class AgentSystemVersionSerializer(serializers.ModelSerializer):
    """Serializer for AgentSystemVersion."""

    snapshots = AgentSystemSnapshotSerializer(many=True, read_only=True)
    created_by_email = serializers.EmailField(
        source='created_by.email', read_only=True, allow_null=True
    )

    class Meta:
        model = AgentSystemVersion
        fields = [
            "id",
            "version",
            "is_active",
            "is_draft",
            "notes",
            "created_at",
            "published_at",
            "created_by",
            "created_by_email",
            "snapshots",
        ]
        read_only_fields = ["id", "created_at", "published_at", "created_by"]


class AgentSystemListSerializer(serializers.ModelSerializer):
    """Serializer for listing AgentSystems."""

    entry_agent_name = serializers.CharField(source='entry_agent.name', read_only=True)
    entry_agent_slug = serializers.CharField(source='entry_agent.slug', read_only=True)
    member_count = serializers.SerializerMethodField()
    active_version = serializers.SerializerMethodField()

    class Meta:
        model = AgentSystem
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "entry_agent",
            "entry_agent_name",
            "entry_agent_slug",
            "is_active",
            "member_count",
            "active_version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_active_version(self, obj):
        version = obj.versions.filter(is_active=True).first()
        if version:
            return {"id": str(version.id), "version": version.version}
        return None


class AgentSystemDetailSerializer(serializers.ModelSerializer):
    """Serializer for AgentSystem detail view."""

    entry_agent_name = serializers.CharField(source='entry_agent.name', read_only=True)
    entry_agent_slug = serializers.CharField(source='entry_agent.slug', read_only=True)
    members = AgentSystemMemberSerializer(many=True, read_only=True)
    versions = AgentSystemVersionSerializer(many=True, read_only=True)
    dependency_graph = serializers.SerializerMethodField()

    class Meta:
        model = AgentSystem
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "entry_agent",
            "entry_agent_name",
            "entry_agent_slug",
            "is_active",
            "members",
            "versions",
            "dependency_graph",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_dependency_graph(self, obj):
        return obj.get_dependency_graph()


class AgentSystemCreateSerializer(serializers.Serializer):
    """Serializer for creating an AgentSystem."""

    slug = serializers.SlugField(max_length=100)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    # Accept both entry_agent_id and entry_agent for flexibility
    entry_agent_id = serializers.UUIDField(
        required=False,
        help_text="ID of the entry point agent",
    )
    entry_agent = serializers.UUIDField(
        required=False,
        help_text="ID of the entry point agent (alias for entry_agent_id)",
    )
    auto_discover = serializers.BooleanField(
        default=True,
        help_text="Automatically discover and add all reachable sub-agents",
    )

    def validate(self, data):
        """Normalize entry_agent to entry_agent_id."""
        # Accept either entry_agent or entry_agent_id
        if 'entry_agent' in data and data['entry_agent']:
            data['entry_agent_id'] = data.pop('entry_agent')
        elif 'entry_agent' in data:
            data.pop('entry_agent')
        return data


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a system."""

    agent_id = serializers.UUIDField(help_text="ID of the agent to add")
    role = serializers.ChoiceField(
        choices=AgentSystemMember.Role.choices,
        default=AgentSystemMember.Role.SPECIALIST,
    )
    notes = serializers.CharField(required=False, default="")


class PublishVersionSerializer(serializers.Serializer):
    """Serializer for publishing a system version."""

    version = serializers.CharField(
        max_length=50,
        help_text="Version string (e.g., '1.0.0', '2024-01-15')",
    )
    notes = serializers.CharField(
        required=False,
        default="",
        help_text="Release notes for this version",
    )
    make_active = serializers.BooleanField(
        default=False,
        help_text="Whether to make this the active version immediately",
    )


# =============================================================================
# Collaborator Serializers for Multi-User Access Control
# =============================================================================


class AgentCollaboratorSerializer(serializers.ModelSerializer):
    """Serializer for AgentCollaborator."""

    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    added_by_email = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    can_view = serializers.BooleanField(read_only=True)
    can_edit = serializers.BooleanField(read_only=True)
    can_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = AgentCollaborator
        fields = [
            "id",
            "agent",
            "user",
            "user_email",
            "user_name",
            "role",
            "role_display",
            "can_view",
            "can_edit",
            "can_admin",
            "added_by",
            "added_by_email",
            "added_at",
            "updated_at",
        ]
        read_only_fields = ["id", "added_by", "added_at", "updated_at"]

    def get_user_email(self, obj):
        """Return email or username as identifier."""
        if obj.user:
            return obj.user.email or getattr(obj.user, 'username', None) or str(obj.user)
        return None

    def get_user_name(self, obj):
        """Return full name, or fall back to email/username."""
        if obj.user:
            if hasattr(obj.user, 'get_full_name'):
                name = obj.user.get_full_name()
                if name:
                    return name
            return obj.user.email or getattr(obj.user, 'username', None) or str(obj.user)
        return None

    def get_added_by_email(self, obj):
        """Return added_by email or username."""
        if obj.added_by:
            return obj.added_by.email or getattr(obj.added_by, 'username', None) or str(obj.added_by)
        return None


class SystemCollaboratorSerializer(serializers.ModelSerializer):
    """Serializer for SystemCollaborator."""

    user_email = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    added_by_email = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    can_view = serializers.BooleanField(read_only=True)
    can_edit = serializers.BooleanField(read_only=True)
    can_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = SystemCollaborator
        fields = [
            "id",
            "system",
            "user",
            "user_email",
            "user_name",
            "role",
            "role_display",
            "can_view",
            "can_edit",
            "can_admin",
            "added_by",
            "added_by_email",
            "added_at",
            "updated_at",
        ]
        read_only_fields = ["id", "added_by", "added_at", "updated_at"]

    def get_user_email(self, obj):
        """Return email or username as identifier."""
        if obj.user:
            return obj.user.email or getattr(obj.user, 'username', None) or str(obj.user)
        return None

    def get_user_name(self, obj):
        """Return full name, or fall back to email/username."""
        if obj.user:
            if hasattr(obj.user, 'get_full_name'):
                name = obj.user.get_full_name()
                if name:
                    return name
            return obj.user.email or getattr(obj.user, 'username', None) or str(obj.user)
        return None

    def get_added_by_email(self, obj):
        """Return added_by email or username."""
        if obj.added_by:
            return obj.added_by.email or getattr(obj.added_by, 'username', None) or str(obj.added_by)
        return None


class AddCollaboratorSerializer(serializers.Serializer):
    """Serializer for adding a collaborator by email or username."""

    email = serializers.CharField(
        help_text="Email or username of the user to add as collaborator"
    )
    role = serializers.ChoiceField(
        choices=CollaboratorRole.choices,
        default=CollaboratorRole.VIEWER,
        help_text="Role to grant: viewer, editor, or admin",
    )


class UpdateCollaboratorRoleSerializer(serializers.Serializer):
    """Serializer for updating a collaborator's role."""

    role = serializers.ChoiceField(
        choices=CollaboratorRole.choices,
        help_text="New role: viewer, editor, or admin",
    )
