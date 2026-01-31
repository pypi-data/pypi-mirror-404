"""
API views for django_agent_studio.
"""

from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
from django_agent_studio.api.serializers import (
    AgentDefinitionListSerializer,
    AgentDefinitionDetailSerializer,
    AgentVersionSerializer,
    AgentToolSerializer,
    AgentKnowledgeSerializer,
    DiscoveredFunctionSerializer,
    DynamicToolSerializer,
    DynamicToolExecutionSerializer,
    ProjectScanRequestSerializer,
    GenerateToolsRequestSerializer,
    # Collaborator serializers
    AgentCollaboratorSerializer,
    SystemCollaboratorSerializer,
    AddCollaboratorSerializer,
    UpdateCollaboratorRoleSerializer,
)


# =============================================================================
# Helper functions for consistent access control
# =============================================================================

from django.db.models import Q


def get_agent_for_user(user, agent_id):
    """
    Get an agent if the user has access.

    - Superusers can access any agent
    - Owners can access their own agents
    - Collaborators can access agents they've been granted access to
    - Users with system access can access agents in that system
    """
    if user.is_superuser:
        return get_object_or_404(AgentDefinition, id=agent_id)

    # Try to get the agent
    agent = get_object_or_404(AgentDefinition, id=agent_id)

    # Check if owner
    if agent.owner == user:
        return agent

    # Check if direct collaborator on agent
    if AgentCollaborator.objects.filter(agent=agent, user=user).exists():
        return agent

    # Check if user has access via a system that contains this agent
    # Get all systems this agent belongs to
    agent_system_ids = AgentSystemMember.objects.filter(
        agent=agent
    ).values_list('system_id', flat=True)

    if agent_system_ids:
        # Check if user owns or is a collaborator on any of these systems
        has_system_access = AgentSystem.objects.filter(
            Q(id__in=agent_system_ids) &
            (Q(owner=user) | Q(collaborators__user=user))
        ).exists()
        if has_system_access:
            return agent

    # No access
    raise Http404("Agent not found")


def get_agent_queryset_for_user(user):
    """
    Get queryset of agents accessible to the user.

    - Superusers can see all agents
    - Regular users see:
      - Owned agents
      - Agents where they are direct collaborators
      - Agents in systems they own or are collaborators on
    """
    if user.is_superuser:
        return AgentDefinition.objects.all()

    # Get system IDs the user has access to (owner or collaborator)
    accessible_system_ids = AgentSystem.objects.filter(
        Q(owner=user) | Q(collaborators__user=user)
    ).values_list('id', flat=True)

    # Get agent IDs that are members of accessible systems
    agents_via_systems = AgentSystemMember.objects.filter(
        system_id__in=accessible_system_ids
    ).values_list('agent_id', flat=True)

    return AgentDefinition.objects.filter(
        Q(owner=user) |
        Q(collaborators__user=user) |
        Q(id__in=agents_via_systems)
    ).distinct()


def get_system_for_user(user, system_id):
    """
    Get a system if the user has access.

    - Superusers can access any system
    - Owners can access their own systems
    - Collaborators can access systems they've been granted access to
    """
    from django_agent_runtime.models import SystemCollaborator

    if user.is_superuser:
        return get_object_or_404(AgentSystem, id=system_id)

    # Try to get the system
    system = get_object_or_404(AgentSystem, id=system_id)

    # Check if owner
    if system.owner == user:
        return system

    # Check if collaborator
    if SystemCollaborator.objects.filter(system=system, user=user).exists():
        return system

    # No access
    raise Http404("System not found")


def get_system_queryset_for_user(user):
    """
    Get queryset of systems accessible to the user.

    - Superusers can see all systems
    - Regular users see owned systems and systems where they are collaborators
    """
    if user.is_superuser:
        return AgentSystem.objects.all()
    return AgentSystem.objects.filter(
        Q(owner=user) | Q(collaborators__user=user)
    ).distinct()


class AgentDefinitionListCreateView(generics.ListCreateAPIView):
    """List and create agent definitions."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentDefinitionListSerializer

    def get_queryset(self):
        return get_agent_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        agent = serializer.save(owner=self.request.user)
        # Create initial draft version
        AgentVersion.objects.create(
            agent=agent,
            version="draft",
            is_draft=True,
            is_active=True,
        )


class AgentDefinitionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an agent definition."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentDefinitionDetailSerializer

    def get_queryset(self):
        return get_agent_queryset_for_user(self.request.user)


class AgentVersionListCreateView(generics.ListCreateAPIView):
    """List and create versions for an agent."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentVersionSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        return agent.versions.all()

    def perform_create(self, serializer):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        serializer.save(agent=agent)


class AgentVersionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an agent version."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentVersionSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        return agent.versions.all()


class AgentVersionActivateView(APIView):
    """Activate a specific version of an agent."""

    permission_classes = [IsAuthenticated]

    def post(self, request, agent_id, pk):
        agent = get_agent_for_user(request.user, agent_id)
        version = get_object_or_404(agent.versions, id=pk)

        # Deactivate all other versions
        agent.versions.update(is_active=False)

        # Activate this version
        version.is_active = True
        version.is_draft = False
        version.published_at = timezone.now()
        version.save()

        return Response(AgentVersionSerializer(version).data)


class AgentToolListCreateView(generics.ListCreateAPIView):
    """List and create tools for an agent."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentToolSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        return agent.tools.all()

    def perform_create(self, serializer):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        serializer.save(agent=agent)


class AgentToolDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an agent tool."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentToolSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        return agent.tools.all()


class AgentKnowledgeListCreateView(generics.ListCreateAPIView):
    """List and create knowledge sources for an agent."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentKnowledgeSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        return agent.knowledge_sources.all()

    def perform_create(self, serializer):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        serializer.save(agent=agent)


class AgentKnowledgeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an agent knowledge source."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentKnowledgeSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs["agent_id"])
        return agent.knowledge_sources.all()


class TemplateAgentListView(generics.ListAPIView):
    """List public template agents."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentDefinitionListSerializer

    def get_queryset(self):
        return AgentDefinition.objects.filter(
            is_template=True,
            is_public=True,
            is_active=True,
        )


class AgentForkView(APIView):
    """Fork an agent (create a copy with the current user as owner)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Get the source agent (must be public template, owned by user, or superuser)
        if request.user.is_superuser:
            source = get_object_or_404(AgentDefinition, id=pk)
        else:
            source = get_object_or_404(
                AgentDefinition.objects.filter(
                    models.Q(owner=request.user) |
                    models.Q(is_template=True, is_public=True)
                ),
                id=pk,
            )

        # Create a copy
        new_agent = AgentDefinition.objects.create(
            name=f"{source.name} (Copy)",
            slug=f"{source.slug}-copy-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            description=source.description,
            icon=source.icon,
            parent=source if source.is_template else source.parent,
            owner=request.user,
            is_public=False,
            is_template=False,
        )

        # Copy the active version
        source_version = source.versions.filter(is_active=True).first()
        if source_version:
            AgentVersion.objects.create(
                agent=new_agent,
                version="draft",
                system_prompt=source_version.system_prompt,
                model=source_version.model,
                model_settings=source_version.model_settings,
                extra_config=source_version.extra_config,
                is_draft=True,
                is_active=True,
            )

        # Copy tools
        for tool in source.tools.filter(is_active=True):
            AgentTool.objects.create(
                agent=new_agent,
                name=tool.name,
                tool_type=tool.tool_type,
                description=tool.description,
                parameters_schema=tool.parameters_schema,
                builtin_ref=tool.builtin_ref,
                subagent=tool.subagent,
                config=tool.config,
                order=tool.order,
            )

        # Copy knowledge (except files - those need to be re-uploaded)
        for knowledge in source.knowledge_sources.filter(is_active=True):
            AgentKnowledge.objects.create(
                agent=new_agent,
                name=knowledge.name,
                knowledge_type=knowledge.knowledge_type,
                content=knowledge.content,
                url=knowledge.url,
                dynamic_config=knowledge.dynamic_config,
                inclusion_mode=knowledge.inclusion_mode,
                order=knowledge.order,
            )

        return Response(
            AgentDefinitionDetailSerializer(new_agent).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# Dynamic Tool Discovery Views
# =============================================================================

from django_agent_studio.api.permissions import (
    CanViewDynamicTools,
    CanScanProject,
    CanRequestTool,
    CanCreateTool,
    CanApproveTool,
    CanManagePermissions,
    DynamicToolObjectPermission,
    IsOwnerOrHasDynamicToolAccess,
)
from django_agent_studio.services.permissions import get_permission_service


class ProjectScanView(APIView):
    """
    Scan the Django project to discover functions.

    POST /api/agents/{id}/scan-project/

    Requires: Scanner access level or agent ownership
    """

    permission_classes = [IsAuthenticated, CanScanProject | IsOwnerOrHasDynamicToolAccess]

    def post(self, request, agent_id):
        agent = get_object_or_404(AgentDefinition, id=agent_id)

        serializer = ProjectScanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django_agent_runtime.dynamic_tools import ProjectScanner

        # Create scanner with options
        scanner = ProjectScanner(
            include_private=serializer.validated_data.get('include_private', False),
            include_tests=serializer.validated_data.get('include_tests', False),
            app_filter=serializer.validated_data.get('app_filter'),
        )

        # Scan project or specific directory
        directory = serializer.validated_data.get('directory')
        if directory:
            functions = scanner.scan_directory(directory)
        else:
            functions = scanner.scan()

        # Store discovered functions
        scan_session = scanner.scan_session
        created_functions = []

        for func_info in functions:
            discovered, created = DiscoveredFunction.objects.update_or_create(
                function_path=func_info.function_path,
                scan_session=scan_session,
                defaults={
                    'name': func_info.name,
                    'module_path': func_info.module_path,
                    'function_type': func_info.function_type,
                    'class_name': func_info.class_name,
                    'file_path': func_info.file_path,
                    'line_number': func_info.line_number,
                    'signature': func_info.signature,
                    'docstring': func_info.docstring,
                    'parameters': func_info.parameters,
                    'return_type': func_info.return_type,
                    'is_async': func_info.is_async,
                    'has_side_effects': func_info.has_side_effects,
                    'is_private': func_info.is_private,
                }
            )
            created_functions.append(discovered)

        return Response({
            'scan_session': scan_session,
            'functions_discovered': len(created_functions),
            'functions': DiscoveredFunctionSerializer(created_functions, many=True).data,
        })


class DiscoveredFunctionListView(generics.ListAPIView):
    """
    List discovered functions from project scans.

    GET /api/discovered-functions/

    Requires: Viewer access level
    """

    permission_classes = [IsAuthenticated, CanViewDynamicTools]
    serializer_class = DiscoveredFunctionSerializer

    def get_queryset(self):
        queryset = DiscoveredFunction.objects.all()

        # Filter by scan session
        scan_session = self.request.query_params.get('scan_session')
        if scan_session:
            queryset = queryset.filter(scan_session=scan_session)

        # Filter by function type
        function_type = self.request.query_params.get('function_type')
        if function_type:
            queryset = queryset.filter(function_type=function_type)

        # Filter by selected status
        is_selected = self.request.query_params.get('is_selected')
        if is_selected is not None:
            queryset = queryset.filter(is_selected=is_selected.lower() == 'true')

        return queryset


class GenerateToolsView(APIView):
    """
    Generate dynamic tools from discovered functions.

    POST /api/agents/{id}/generate-tools/

    Requires:
    - Creator access: creates tools directly
    - Requester access: creates approval requests instead
    - Owner: creates tools directly
    """

    permission_classes = [IsAuthenticated, CanRequestTool | IsOwnerOrHasDynamicToolAccess]

    def post(self, request, agent_id):
        agent = get_object_or_404(AgentDefinition, id=agent_id)

        # Check if user can create directly or needs approval
        perm_service = get_permission_service()
        can_create_directly = (
            agent.owner == request.user or
            perm_service.can_create_tool(request.user, agent)
        )

        serializer = GenerateToolsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django_agent_runtime.dynamic_tools import ToolGenerator

        # Get discovered functions
        function_ids = serializer.validated_data['function_ids']
        functions = DiscoveredFunction.objects.filter(id__in=function_ids)

        if not functions.exists():
            return Response(
                {'error': 'No functions found with the provided IDs'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create generator
        generator = ToolGenerator(
            default_requires_confirmation=serializer.validated_data.get(
                'requires_confirmation', True
            ),
            name_prefix=serializer.validated_data.get('name_prefix', ''),
        )

        if can_create_directly:
            # Create tools directly
            return self._create_tools_directly(
                request, agent, functions, generator, serializer
            )
        else:
            # Create approval requests
            return self._create_approval_requests(
                request, agent, functions, generator, serializer
            )

    def _create_tools_directly(self, request, agent, functions, generator, serializer):
        """Create tools directly (for owners and creators)."""
        from django_agent_runtime.dynamic_tools.scanner import FunctionInfo

        created_tools = []
        for discovered in functions:
            func_info = FunctionInfo(
                name=discovered.name,
                module_path=discovered.module_path,
                function_path=discovered.function_path,
                function_type=discovered.function_type,
                file_path=discovered.file_path,
                line_number=discovered.line_number,
                signature=discovered.signature,
                docstring=discovered.docstring,
                class_name=discovered.class_name,
                parameters=discovered.parameters,
                return_type=discovered.return_type,
                is_async=discovered.is_async,
                has_side_effects=discovered.has_side_effects,
                is_private=discovered.is_private,
            )

            schema = generator.generate(func_info)

            tool, created = DynamicTool.objects.update_or_create(
                agent=agent,
                function_path=schema.function_path,
                defaults={
                    'name': schema.name,
                    'description': schema.description,
                    'parameters_schema': schema.parameters_schema,
                    'source_file': schema.source_file,
                    'source_line': schema.source_line,
                    'is_safe': schema.is_safe,
                    'requires_confirmation': schema.requires_confirmation,
                    'discovered_function': discovered,
                    'created_by': request.user,
                }
            )

            discovered.is_selected = True
            discovered.save(update_fields=['is_selected'])
            created_tools.append(tool)

        return Response({
            'tools_created': len(created_tools),
            'tools': DynamicToolSerializer(created_tools, many=True).data,
        }, status=status.HTTP_201_CREATED)

    def _create_approval_requests(self, request, agent, functions, generator, serializer):
        """Create approval requests (for requesters)."""
        from django_agent_runtime.dynamic_tools.scanner import FunctionInfo
        from django_agent_studio.models import ToolApprovalRequest
        from django_agent_studio.api.serializers import ToolApprovalRequestSerializer

        created_requests = []
        for discovered in functions:
            func_info = FunctionInfo(
                name=discovered.name,
                module_path=discovered.module_path,
                function_path=discovered.function_path,
                function_type=discovered.function_type,
                file_path=discovered.file_path,
                line_number=discovered.line_number,
                signature=discovered.signature,
                docstring=discovered.docstring,
                class_name=discovered.class_name,
                parameters=discovered.parameters,
                return_type=discovered.return_type,
                is_async=discovered.is_async,
                has_side_effects=discovered.has_side_effects,
                is_private=discovered.is_private,
            )

            schema = generator.generate(func_info)

            approval_request = ToolApprovalRequest.objects.create(
                agent=agent,
                discovered_function=discovered,
                proposed_name=schema.name,
                proposed_description=schema.description,
                proposed_is_safe=schema.is_safe,
                proposed_requires_confirmation=schema.requires_confirmation,
                proposed_timeout_seconds=30,
                requester=request.user,
                request_reason=serializer.validated_data.get('request_reason', ''),
            )
            created_requests.append(approval_request)

        return Response({
            'approval_required': True,
            'requests_created': len(created_requests),
            'requests': ToolApprovalRequestSerializer(created_requests, many=True).data,
        }, status=status.HTTP_202_ACCEPTED)


class DynamicToolListView(generics.ListAPIView):
    """
    List dynamic tools for an agent.

    GET /api/agents/{id}/dynamic-tools/

    Requires: Viewer access or agent ownership
    """

    permission_classes = [IsAuthenticated, CanViewDynamicTools | IsOwnerOrHasDynamicToolAccess]
    serializer_class = DynamicToolSerializer

    def get_queryset(self):
        agent = get_object_or_404(AgentDefinition, id=self.kwargs["agent_id"])
        return agent.dynamic_tools.all()


class DynamicToolDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a dynamic tool.

    GET/PUT/PATCH/DELETE /api/agents/{id}/dynamic-tools/{tool_id}/

    Requires:
    - GET: Viewer access or ownership
    - PUT/PATCH: Creator access or ownership
    - DELETE: Admin access or ownership
    """

    permission_classes = [IsAuthenticated, DynamicToolObjectPermission | IsOwnerOrHasDynamicToolAccess]
    serializer_class = DynamicToolSerializer

    def get_queryset(self):
        agent = get_object_or_404(AgentDefinition, id=self.kwargs["agent_id"])
        return agent.dynamic_tools.all()


class DynamicToolToggleView(APIView):
    """
    Toggle a dynamic tool's active status.

    POST /api/agents/{id}/dynamic-tools/{tool_id}/toggle/

    Requires: Creator access or ownership
    """

    permission_classes = [IsAuthenticated, CanCreateTool | IsOwnerOrHasDynamicToolAccess]

    def post(self, request, agent_id, tool_id):
        agent = get_object_or_404(AgentDefinition, id=agent_id)
        tool = get_object_or_404(agent.dynamic_tools, id=tool_id)

        tool.is_active = not tool.is_active
        tool.save(update_fields=['is_active'])

        return Response(DynamicToolSerializer(tool).data)


class DynamicToolExecutionListView(generics.ListAPIView):
    """
    List executions for a dynamic tool.

    GET /api/agents/{id}/dynamic-tools/{tool_id}/executions/

    Requires: Viewer access or ownership
    """

    permission_classes = [IsAuthenticated, CanViewDynamicTools | IsOwnerOrHasDynamicToolAccess]
    serializer_class = DynamicToolExecutionSerializer

    def get_queryset(self):
        agent = get_object_or_404(AgentDefinition, id=self.kwargs["agent_id"])
        tool = get_object_or_404(agent.dynamic_tools, id=self.kwargs["tool_id"])
        return tool.executions.all()


# =============================================================================
# Approval Workflow Views
# =============================================================================

from django_agent_studio.models import ToolApprovalRequest, UserDynamicToolAccess
from django_agent_studio.api.serializers import (
    ToolApprovalRequestSerializer,
    ToolApprovalReviewSerializer,
    UserDynamicToolAccessSerializer,
    GrantAccessSerializer,
)


class ToolApprovalRequestListView(generics.ListAPIView):
    """
    List tool approval requests.

    GET /api/tool-approval-requests/

    - Admins see all pending requests
    - Requesters see their own requests
    """

    permission_classes = [IsAuthenticated, CanRequestTool]
    serializer_class = ToolApprovalRequestSerializer

    def get_queryset(self):
        perm_service = get_permission_service()

        # Admins see all, others see only their own
        if perm_service.can_approve(self.request.user):
            queryset = ToolApprovalRequest.objects.all()
        else:
            queryset = ToolApprovalRequest.objects.filter(requester=self.request.user)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by agent
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)

        return queryset


class ToolApprovalRequestDetailView(generics.RetrieveAPIView):
    """
    Retrieve a tool approval request.

    GET /api/tool-approval-requests/{id}/
    """

    permission_classes = [IsAuthenticated, CanRequestTool]
    serializer_class = ToolApprovalRequestSerializer

    def get_queryset(self):
        perm_service = get_permission_service()

        if perm_service.can_approve(self.request.user):
            return ToolApprovalRequest.objects.all()
        return ToolApprovalRequest.objects.filter(requester=self.request.user)


class ToolApprovalReviewView(APIView):
    """
    Review (approve/reject) a tool approval request.

    POST /api/tool-approval-requests/{id}/review/

    Requires: Admin access
    """

    permission_classes = [IsAuthenticated, CanApproveTool]

    def post(self, request, pk):
        approval_request = get_object_or_404(ToolApprovalRequest, id=pk)

        if approval_request.status != ToolApprovalRequest.Status.PENDING:
            return Response(
                {'error': f'Request is already {approval_request.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ToolApprovalReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        review_notes = serializer.validated_data.get('review_notes', '')

        approval_request.reviewed_by = request.user
        approval_request.reviewed_at = timezone.now()
        approval_request.review_notes = review_notes

        if action == 'approve':
            return self._approve_request(approval_request, serializer.validated_data)
        else:
            return self._reject_request(approval_request)

    def _approve_request(self, approval_request, validated_data):
        """Approve the request and create the tool."""
        # Use overrides if provided, otherwise use proposed values
        name = validated_data.get('override_name', approval_request.proposed_name)
        description = validated_data.get(
            'override_description', approval_request.proposed_description
        )
        is_safe = validated_data.get('override_is_safe', approval_request.proposed_is_safe)
        requires_confirmation = validated_data.get(
            'override_requires_confirmation',
            approval_request.proposed_requires_confirmation
        )
        timeout = validated_data.get(
            'override_timeout_seconds',
            approval_request.proposed_timeout_seconds
        )

        # Create the tool
        tool = DynamicTool.objects.create(
            agent=approval_request.agent,
            name=name,
            description=description,
            function_path=approval_request.discovered_function.function_path,
            source_file=approval_request.discovered_function.file_path,
            source_line=approval_request.discovered_function.line_number,
            parameters_schema=self._build_parameters_schema(
                approval_request.discovered_function
            ),
            is_safe=is_safe,
            requires_confirmation=requires_confirmation,
            timeout_seconds=timeout,
            discovered_function=approval_request.discovered_function,
            created_by=approval_request.requester,
            is_verified=True,  # Admin-approved tools are verified
        )

        # Update request
        approval_request.status = ToolApprovalRequest.Status.APPROVED
        approval_request.created_tool = tool
        approval_request.save()

        # Mark function as selected
        approval_request.discovered_function.is_selected = True
        approval_request.discovered_function.save(update_fields=['is_selected'])

        return Response({
            'status': 'approved',
            'tool': DynamicToolSerializer(tool).data,
            'request': ToolApprovalRequestSerializer(approval_request).data,
        })

    def _reject_request(self, approval_request):
        """Reject the request."""
        approval_request.status = ToolApprovalRequest.Status.REJECTED
        approval_request.save()

        return Response({
            'status': 'rejected',
            'request': ToolApprovalRequestSerializer(approval_request).data,
        })

    def _build_parameters_schema(self, discovered_function):
        """Build JSON Schema from discovered function parameters."""
        from django_agent_runtime.dynamic_tools import ToolGenerator
        from django_agent_runtime.dynamic_tools.scanner import FunctionInfo

        func_info = FunctionInfo(
            name=discovered_function.name,
            module_path=discovered_function.module_path,
            function_path=discovered_function.function_path,
            function_type=discovered_function.function_type,
            file_path=discovered_function.file_path,
            line_number=discovered_function.line_number,
            signature=discovered_function.signature,
            docstring=discovered_function.docstring,
            class_name=discovered_function.class_name,
            parameters=discovered_function.parameters,
            return_type=discovered_function.return_type,
            is_async=discovered_function.is_async,
            has_side_effects=discovered_function.has_side_effects,
            is_private=discovered_function.is_private,
        )

        generator = ToolGenerator()
        schema = generator.generate(func_info)
        return schema.parameters_schema


class ToolApprovalCancelView(APIView):
    """
    Cancel a pending tool approval request.

    POST /api/tool-approval-requests/{id}/cancel/

    Only the requester can cancel their own request.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        approval_request = get_object_or_404(
            ToolApprovalRequest,
            id=pk,
            requester=request.user,
        )

        if approval_request.status != ToolApprovalRequest.Status.PENDING:
            return Response(
                {'error': f'Request is already {approval_request.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        approval_request.status = ToolApprovalRequest.Status.CANCELLED
        approval_request.save()

        return Response({
            'status': 'cancelled',
            'request': ToolApprovalRequestSerializer(approval_request).data,
        })



# =============================================================================
# Permission Management Views
# =============================================================================


class UserAccessListView(generics.ListAPIView):
    """
    List all user access grants.

    GET /api/dynamic-tool-access/

    Requires: Admin access
    """

    permission_classes = [IsAuthenticated, CanManagePermissions]
    serializer_class = UserDynamicToolAccessSerializer
    queryset = UserDynamicToolAccess.objects.all()


class UserAccessDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a user's access.

    GET/PUT/PATCH/DELETE /api/dynamic-tool-access/{id}/

    Requires: Admin access
    """

    permission_classes = [IsAuthenticated, CanManagePermissions]
    serializer_class = UserDynamicToolAccessSerializer
    queryset = UserDynamicToolAccess.objects.all()


class GrantAccessView(APIView):
    """
    Grant dynamic tool access to a user.

    POST /api/dynamic-tool-access/grant/

    Requires: Admin access
    """

    permission_classes = [IsAuthenticated, CanManagePermissions]

    def post(self, request):
        serializer = GrantAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get agents if restricted
        agents = None
        agent_ids = serializer.validated_data.get('restricted_to_agent_ids')
        if agent_ids:
            agents = AgentDefinition.objects.filter(id__in=agent_ids)

        perm_service = get_permission_service()
        access = perm_service.grant_access(
            user=user,
            access_level=serializer.validated_data['access_level'],
            granted_by=request.user,
            agents=agents,
            notes=serializer.validated_data.get('notes', ''),
        )

        return Response(
            UserDynamicToolAccessSerializer(access).data,
            status=status.HTTP_201_CREATED,
        )


class RevokeAccessView(APIView):
    """
    Revoke dynamic tool access from a user.

    POST /api/dynamic-tool-access/revoke/

    Requires: Admin access
    """

    permission_classes = [IsAuthenticated, CanManagePermissions]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        perm_service = get_permission_service()
        revoked = perm_service.revoke_access(user)

        if revoked:
            return Response({'status': 'revoked'})
        return Response(
            {'status': 'no_access', 'message': 'User had no access to revoke'},
        )


class MyAccessView(APIView):
    """
    Get the current user's dynamic tool access level.

    GET /api/dynamic-tool-access/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        perm_service = get_permission_service()
        access_level = perm_service.get_user_access_level(request.user)

        # Get the access record if it exists
        try:
            access = UserDynamicToolAccess.objects.get(user=request.user)
            return Response({
                'access_level': access_level,
                'access_level_display': access.get_access_level_display(),
                'restricted_to_agents': [
                    {'id': str(a.id), 'name': a.name}
                    for a in access.restricted_to_agents.all()
                ],
                'granted_at': access.granted_at,
            })
        except UserDynamicToolAccess.DoesNotExist:
            # User has no explicit access (defaults to NONE unless superuser)
            from django_agent_studio.models.permissions import DynamicToolAccessLevel
            return Response({
                'access_level': access_level,
                'access_level_display': (
                    'Admin (superuser)' if request.user.is_superuser
                    else DynamicToolAccessLevel(access_level).label
                ),
                'restricted_to_agents': [],
                'granted_at': None,
            })


class ModelsListView(APIView):
    """List available LLM models for the model selector."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django_agent_runtime.runtime.llm import list_models_for_ui, DEFAULT_MODEL

        models = list_models_for_ui()
        return Response({
            "models": models,
            "default": DEFAULT_MODEL,
        })


# =============================================================================
# Agent Schema Editor Views
# =============================================================================


class AgentFullSchemaView(APIView):
    """
    Get or update the complete agent schema for debugging/editing.

    GET /api/agents/{id}/full-schema/
    Returns the complete agent configuration including all tools, knowledge,
    dynamic tools, discovered functions, RAG config, etc.

    PUT /api/agents/{id}/full-schema/
    Updates the agent configuration from a full schema JSON.
    """

    permission_classes = [IsAuthenticated]

    def _get_memory_config(self, version):
        """Extract memory configuration from version's extra_config."""
        if not version:
            return self._default_memory_config()

        extra = version.extra_config or {}
        return {
            "enabled": extra.get("memory_enabled", True),
            "default_scope": extra.get("memory_default_scope", "user"),
            "allowed_scopes": extra.get("memory_allowed_scopes", ["conversation", "user", "system"]),
            "auto_recall": extra.get("memory_auto_recall", True),
            "max_memories_in_prompt": extra.get("memory_max_in_prompt", 50),
            "include_system_memories": extra.get("memory_include_system", True),
            "retention_days": extra.get("memory_retention_days", None),
        }

    def _default_memory_config(self):
        """Return default memory configuration."""
        return {
            "enabled": True,
            "default_scope": "user",
            "allowed_scopes": ["conversation", "user", "system"],
            "auto_recall": True,
            "max_memories_in_prompt": 50,
            "include_system_memories": True,
            "retention_days": None,
        }

    def get(self, request, pk):
        """Get the complete agent schema."""
        agent = get_agent_for_user(request.user, pk)

        # Get active version
        active_version = agent.versions.filter(is_active=True).first()

        # Build comprehensive schema
        schema = {
            # Metadata
            "id": str(agent.id),
            "slug": agent.slug,
            "name": agent.name,
            "description": agent.description,
            "icon": agent.icon,
            "is_public": agent.is_public,
            "is_template": agent.is_template,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,

            # Parent agent (for inheritance)
            "parent": {
                "id": str(agent.parent.id),
                "slug": agent.parent.slug,
                "name": agent.parent.name,
            } if agent.parent else None,

            # Active version configuration
            "version": {
                "id": str(active_version.id) if active_version else None,
                "version": active_version.version if active_version else "draft",
                "system_prompt": active_version.system_prompt if active_version else "",
                "model": active_version.model if active_version else "gpt-4o",
                "model_settings": active_version.model_settings if active_version else {},
                "extra_config": active_version.extra_config if active_version else {},
                "is_draft": active_version.is_draft if active_version else True,
                "is_active": active_version.is_active if active_version else False,
                "notes": active_version.notes if active_version else "",
            },

            # RAG configuration
            "rag_config": agent.rag_config or {
                "enabled": False,
                "top_k": 5,
                "similarity_threshold": 0.7,
                "chunk_size": 500,
                "chunk_overlap": 50,
                "embedding_model": "text-embedding-3-small",
            },

            # File upload/processing configuration
            "file_config": agent.file_config or {
                "enabled": False,
                "max_file_size_mb": 100,
                "allowed_types": ["image/*", "application/pdf", "text/*"],
                "ocr_provider": None,
                "vision_provider": None,
                "enable_thumbnails": True,
                "storage_path": None,
            },

            # Memory configuration (from extra_config)
            "memory_config": self._get_memory_config(active_version),

            # Static tools (AgentTool)
            "tools": [
                {
                    "id": str(tool.id),
                    "name": tool.name,
                    "tool_type": tool.tool_type,
                    "description": tool.description,
                    "parameters_schema": tool.parameters_schema,
                    "builtin_ref": tool.builtin_ref,
                    "subagent_id": str(tool.subagent_id) if tool.subagent_id else None,
                    "config": tool.config,
                    "is_active": tool.is_active,
                    "order": tool.order,
                }
                for tool in agent.tools.all().order_by('order', 'name')
            ],

            # Dynamic tools (from function discovery)
            "dynamic_tools": [
                {
                    "id": str(dt.id),
                    "name": dt.name,
                    "description": dt.description,
                    "function_path": dt.function_path,
                    "source_file": dt.source_file,
                    "source_line": dt.source_line,
                    "parameters_schema": dt.parameters_schema,
                    "execution_mode": dt.execution_mode,
                    "timeout_seconds": dt.timeout_seconds,
                    "is_safe": dt.is_safe,
                    "requires_confirmation": dt.requires_confirmation,
                    "allowed_for_auto_execution": dt.allowed_for_auto_execution,
                    "allowed_imports": dt.allowed_imports,
                    "blocked_imports": dt.blocked_imports,
                    "is_active": dt.is_active,
                    "is_verified": dt.is_verified,
                    "version": dt.version,
                }
                for dt in agent.dynamic_tools.all().order_by('name')
            ],

            # Knowledge sources
            "knowledge": [
                {
                    "id": str(k.id),
                    "name": k.name,
                    "knowledge_type": k.knowledge_type,
                    "content": k.content if k.knowledge_type == 'text' else None,
                    "url": k.url if k.knowledge_type == 'url' else None,
                    "file": k.file.url if k.file else None,
                    "dynamic_config": k.dynamic_config if k.knowledge_type == 'dynamic' else None,
                    "inclusion_mode": k.inclusion_mode,
                    "is_active": k.is_active,
                    "order": k.order,
                    # RAG-specific fields
                    "embedding_status": k.embedding_status,
                    "chunk_count": k.chunk_count,
                    "indexed_at": k.indexed_at.isoformat() if k.indexed_at else None,
                    "rag_config": k.rag_config,
                }
                for k in agent.knowledge_sources.all().order_by('order', 'name')
            ],

            # Available discovered functions (not yet converted to tools)
            "available_functions": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "module_path": f.module_path,
                    "function_path": f.function_path,
                    "function_type": f.function_type,
                    "class_name": f.class_name,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "signature": f.signature,
                    "docstring": f.docstring,
                    "parameters": f.parameters,
                    "return_type": f.return_type,
                    "is_async": f.is_async,
                    "has_side_effects": f.has_side_effects,
                    "is_private": f.is_private,
                    "is_selected": f.is_selected,
                }
                for f in DiscoveredFunction.objects.filter(is_selected=False).order_by('module_path', 'name')[:100]
            ],

            # Effective config (merged with parent)
            "effective_config": agent.get_effective_config(),

            # Portable config format (for export)
            "portable_config": agent.to_config_dict(),
        }

        return Response(schema)

    def put(self, request, pk):
        """Update the agent configuration from a full schema."""
        agent = get_agent_for_user(request.user, pk)

        data = request.data

        # Update agent metadata
        if 'name' in data:
            agent.name = data['name']
        if 'description' in data:
            agent.description = data['description']
        if 'icon' in data:
            agent.icon = data['icon']
        if 'is_public' in data:
            agent.is_public = data['is_public']
        if 'is_template' in data:
            agent.is_template = data['is_template']
        if 'is_active' in data:
            agent.is_active = data['is_active']
        if 'rag_config' in data:
            agent.rag_config = data['rag_config']
        if 'file_config' in data:
            agent.file_config = data['file_config']

        agent.save()

        # Update active version
        if 'version' in data:
            version_data = data['version']
            active_version = agent.versions.filter(is_active=True).first()

            if active_version:
                if 'system_prompt' in version_data:
                    active_version.system_prompt = version_data['system_prompt']
                if 'model' in version_data:
                    active_version.model = version_data['model']
                if 'model_settings' in version_data:
                    active_version.model_settings = version_data['model_settings']
                if 'extra_config' in version_data:
                    active_version.extra_config = version_data['extra_config']
                if 'notes' in version_data:
                    active_version.notes = version_data['notes']
                active_version.save()

        # Update memory configuration
        if 'memory_config' in data:
            active_version = agent.versions.filter(is_active=True).first()
            if active_version:
                mem_config = data['memory_config']
                if active_version.extra_config is None:
                    active_version.extra_config = {}
                # Map memory_config fields to extra_config keys
                if 'enabled' in mem_config:
                    active_version.extra_config['memory_enabled'] = mem_config['enabled']
                if 'default_scope' in mem_config:
                    active_version.extra_config['memory_default_scope'] = mem_config['default_scope']
                if 'allowed_scopes' in mem_config:
                    active_version.extra_config['memory_allowed_scopes'] = mem_config['allowed_scopes']
                if 'auto_recall' in mem_config:
                    active_version.extra_config['memory_auto_recall'] = mem_config['auto_recall']
                if 'max_memories_in_prompt' in mem_config:
                    active_version.extra_config['memory_max_in_prompt'] = mem_config['max_memories_in_prompt']
                if 'include_system_memories' in mem_config:
                    active_version.extra_config['memory_include_system'] = mem_config['include_system_memories']
                if 'retention_days' in mem_config:
                    active_version.extra_config['memory_retention_days'] = mem_config['retention_days']
                active_version.save()

        # Update tools
        if 'tools' in data:
            for tool_data in data['tools']:
                if 'id' in tool_data:
                    try:
                        tool = agent.tools.get(id=tool_data['id'])
                        for field in ['name', 'description', 'tool_type', 'parameters_schema',
                                      'builtin_ref', 'config', 'is_active', 'order']:
                            if field in tool_data:
                                setattr(tool, field, tool_data[field])
                        tool.save()
                    except AgentTool.DoesNotExist:
                        pass
                else:
                    # Create new tool
                    AgentTool.objects.create(
                        agent=agent,
                        name=tool_data.get('name', 'new_tool'),
                        tool_type=tool_data.get('tool_type', 'function'),
                        description=tool_data.get('description', ''),
                        parameters_schema=tool_data.get('parameters_schema', {}),
                        builtin_ref=tool_data.get('builtin_ref', ''),
                        config=tool_data.get('config', {}),
                        is_active=tool_data.get('is_active', True),
                        order=tool_data.get('order', 0),
                    )

        # Update dynamic tools
        if 'dynamic_tools' in data:
            for dt_data in data['dynamic_tools']:
                if 'id' in dt_data:
                    try:
                        dt = agent.dynamic_tools.get(id=dt_data['id'])
                        for field in ['name', 'description', 'function_path', 'parameters_schema',
                                      'execution_mode', 'timeout_seconds', 'is_safe',
                                      'requires_confirmation', 'allowed_for_auto_execution',
                                      'allowed_imports', 'blocked_imports', 'is_active', 'is_verified']:
                            if field in dt_data:
                                setattr(dt, field, dt_data[field])
                        dt.save()
                    except DynamicTool.DoesNotExist:
                        pass

        # Update knowledge sources
        if 'knowledge' in data:
            for k_data in data['knowledge']:
                if 'id' in k_data:
                    try:
                        k = agent.knowledge_sources.get(id=k_data['id'])
                        for field in ['name', 'knowledge_type', 'content', 'url',
                                      'dynamic_config', 'inclusion_mode', 'is_active',
                                      'order', 'rag_config']:
                            if field in k_data:
                                setattr(k, field, k_data[field])
                        k.save()
                    except AgentKnowledge.DoesNotExist:
                        pass

        # Create a revision to track this change
        from django_agent_runtime.models import AgentRevision
        AgentRevision.create_from_agent(
            agent,
            comment=f"Updated via schema editor by {request.user.email}",
            user=request.user,
        )

        return Response({
            "status": "updated",
            "message": "Agent schema updated successfully",
        })


# =============================================================================
# Multi-Agent System Views
# =============================================================================

from django_agent_studio.api.serializers import (
    AgentSystemListSerializer,
    AgentSystemDetailSerializer,
    AgentSystemCreateSerializer,
    AgentSystemMemberSerializer,
    AgentSystemVersionSerializer,
    AddMemberSerializer,
    PublishVersionSerializer,
)


class AgentSystemListCreateView(generics.ListCreateAPIView):
    """List and create agent systems."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AgentSystemCreateSerializer
        return AgentSystemListSerializer

    def get_queryset(self):
        return get_system_queryset_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entry_agent_id = serializer.validated_data.get('entry_agent_id')

        if entry_agent_id:
            # Get the entry agent and use the service to create with auto-discovery
            entry_agent = get_agent_for_user(request.user, entry_agent_id)

            from django_agent_runtime.services.multi_agent import create_system_from_entry_agent

            system = create_system_from_entry_agent(
                slug=serializer.validated_data['slug'],
                name=serializer.validated_data['name'],
                entry_agent=entry_agent,
                description=serializer.validated_data.get('description', ''),
                owner=request.user,
                auto_discover=serializer.validated_data.get('auto_discover', True),
            )
        else:
            # Create system without entry agent - can be set later
            system = AgentSystem.objects.create(
                slug=serializer.validated_data['slug'],
                name=serializer.validated_data['name'],
                description=serializer.validated_data.get('description', ''),
                owner=request.user,
            )

        return Response(
            AgentSystemDetailSerializer(system).data,
            status=status.HTTP_201_CREATED,
        )


class AgentSystemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an agent system."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentSystemDetailSerializer

    def get_queryset(self):
        return get_system_queryset_for_user(self.request.user)


class AgentSystemMemberListCreateView(generics.ListCreateAPIView):
    """List and add members to a system."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddMemberSerializer
        return AgentSystemMemberSerializer

    def get_queryset(self):
        system = get_system_for_user(self.request.user, self.kwargs['system_id'])
        return system.members.select_related('agent').all()

    def create(self, request, *args, **kwargs):
        system = get_system_for_user(request.user, self.kwargs['system_id'])

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agent = get_agent_for_user(request.user, serializer.validated_data['agent_id'])

        from django_agent_runtime.services.multi_agent import add_agent_to_system

        member = add_agent_to_system(
            system=system,
            agent=agent,
            role=serializer.validated_data.get('role', AgentSystemMember.Role.SPECIALIST),
            notes=serializer.validated_data.get('notes', ''),
        )

        return Response(
            AgentSystemMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class AgentSystemMemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a system member."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentSystemMemberSerializer

    def get_queryset(self):
        system = get_system_for_user(self.request.user, self.kwargs['system_id'])
        return system.members.all()


class AgentSystemVersionListView(generics.ListAPIView):
    """List versions of a system."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentSystemVersionSerializer

    def get_queryset(self):
        system = get_system_for_user(self.request.user, self.kwargs['system_id'])
        return system.versions.all()


class AgentSystemPublishView(APIView):
    """Publish a new version of a system."""

    permission_classes = [IsAuthenticated]

    def post(self, request, system_id):
        system = get_system_for_user(request.user, system_id)

        serializer = PublishVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django_agent_runtime.services.multi_agent import publish_system_version

        version = publish_system_version(
            system=system,
            version=serializer.validated_data['version'],
            notes=serializer.validated_data.get('notes', ''),
            user=request.user,
            make_active=serializer.validated_data.get('make_active', False),
        )

        return Response(
            AgentSystemVersionSerializer(version).data,
            status=status.HTTP_201_CREATED,
        )


class AgentSystemDeployView(APIView):
    """Deploy (activate) a system version."""

    permission_classes = [IsAuthenticated]

    def post(self, request, system_id, version_id):
        system = get_system_for_user(request.user, system_id)
        version = get_object_or_404(system.versions, id=version_id)

        from django_agent_runtime.services.multi_agent import deploy_system_version

        deploy_system_version(version)

        return Response(AgentSystemVersionSerializer(version).data)


class AgentSystemExportView(APIView):
    """Export a system version as portable JSON."""

    permission_classes = [IsAuthenticated]

    def get(self, request, system_id, version_id):
        system = get_system_for_user(request.user, system_id)
        version = get_object_or_404(system.versions, id=version_id)

        embed_agents = request.query_params.get('embed', 'true').lower() == 'true'

        from django_agent_runtime.services.multi_agent import export_system_version

        config = export_system_version(version, embed_agents=embed_agents)

        return Response(config)


class AgentSystemDiscoverView(APIView):
    """Discover all agents reachable from an entry agent."""

    permission_classes = [IsAuthenticated]

    def get(self, request, agent_id):
        agent = get_agent_for_user(request.user, agent_id)

        from django_agent_runtime.services.multi_agent import discover_system_agents

        agents = discover_system_agents(agent)

        return Response({
            'entry_agent': {
                'id': str(agent.id),
                'slug': agent.slug,
                'name': agent.name,
            },
            'discovered_agents': [
                {
                    'id': str(a.id),
                    'slug': a.slug,
                    'name': a.name,
                    'description': a.description,
                }
                for a in agents
            ],
            'total_count': len(agents),
        })


# =============================================================================
# Spec Document Views
# =============================================================================

class SpecDocumentListCreateView(APIView):
    """List all spec documents or create a new one."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django_agent_runtime.models import SpecDocument

        root_only = request.query_params.get('root_only', 'false').lower() == 'true'
        linked_only = request.query_params.get('linked_only', 'false').lower() == 'true'

        if root_only:
            docs = SpecDocument.objects.filter(parent__isnull=True).select_related('linked_agent').order_by('order', 'title')
        else:
            docs = SpecDocument.objects.all().select_related('linked_agent', 'parent').order_by('parent_id', 'order', 'title')

        if linked_only:
            docs = docs.filter(linked_agent__isnull=False)

        result = []
        for doc in docs:
            item = {
                'id': str(doc.id),
                'title': doc.title,
                'parent_id': str(doc.parent_id) if doc.parent_id else None,
                'order': doc.order,
                'current_version': doc.current_version,
                'has_content': bool(doc.content),
                'content_preview': doc.content[:100] + '...' if len(doc.content) > 100 else doc.content,
                'created_at': doc.created_at.isoformat(),
                'updated_at': doc.updated_at.isoformat(),
            }
            if doc.linked_agent:
                item['linked_agent'] = {
                    'id': str(doc.linked_agent.id),
                    'slug': doc.linked_agent.slug,
                    'name': doc.linked_agent.name,
                }
            result.append(item)

        return Response({'documents': result, 'count': len(result)})

    def post(self, request):
        from django_agent_runtime.models import SpecDocument

        title = request.data.get('title')
        if not title:
            return Response({'error': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)

        content = request.data.get('content', '')
        parent_id = request.data.get('parent_id')
        linked_agent_id = request.data.get('linked_agent_id')
        order = request.data.get('order', 0)

        parent = None
        if parent_id:
            try:
                parent = SpecDocument.objects.get(id=parent_id)
            except SpecDocument.DoesNotExist:
                return Response({'error': f'Parent document not found: {parent_id}'}, status=status.HTTP_404_NOT_FOUND)

        linked_agent = None
        if linked_agent_id:
            try:
                linked_agent = AgentDefinition.objects.get(id=linked_agent_id)
            except AgentDefinition.DoesNotExist:
                return Response({'error': f'Agent not found: {linked_agent_id}'}, status=status.HTTP_404_NOT_FOUND)

        doc = SpecDocument.objects.create(
            title=title,
            content=content,
            parent=parent,
            linked_agent=linked_agent,
            order=order,
            owner=request.user,
        )

        return Response({
            'id': str(doc.id),
            'title': doc.title,
            'current_version': doc.current_version,
            'message': f'Created spec document: {title}',
        }, status=status.HTTP_201_CREATED)


class SpecDocumentDetailView(APIView):
    """Get, update, or delete a spec document."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from django_agent_runtime.models import SpecDocument

        try:
            doc = SpecDocument.objects.select_related('linked_agent', 'parent').get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        include_children = request.query_params.get('include_children', 'false').lower() == 'true'
        render_markdown = request.query_params.get('render_markdown', 'false').lower() == 'true'

        result = {
            'id': str(doc.id),
            'title': doc.title,
            'content': doc.content,
            'parent_id': str(doc.parent_id) if doc.parent_id else None,
            'order': doc.order,
            'current_version': doc.current_version,
            'full_path': doc.get_full_path(),
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
        }

        if doc.linked_agent:
            result['linked_agent'] = {
                'id': str(doc.linked_agent.id),
                'slug': doc.linked_agent.slug,
                'name': doc.linked_agent.name,
            }

        if include_children:
            descendants = doc.get_descendants()
            result['children'] = [
                {
                    'id': str(d.id),
                    'title': d.title,
                    'parent_id': str(d.parent_id) if d.parent_id else None,
                    'has_content': bool(d.content),
                    'linked_agent_slug': d.linked_agent.slug if d.linked_agent else None,
                }
                for d in descendants
            ]

        if render_markdown:
            result['rendered_markdown'] = doc.render_tree_as_markdown()

        return Response(result)

    def put(self, request, pk):
        from django_agent_runtime.models import SpecDocument

        try:
            doc = SpecDocument.objects.get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        changes = []
        if 'title' in request.data:
            doc.title = request.data['title']
            changes.append('title')
        if 'content' in request.data:
            doc.content = request.data['content']
            changes.append('content')
        if 'order' in request.data:
            doc.order = request.data['order']
            changes.append('order')
        if 'parent_id' in request.data:
            parent_id = request.data['parent_id']
            if parent_id:
                try:
                    doc.parent = SpecDocument.objects.get(id=parent_id)
                except SpecDocument.DoesNotExist:
                    return Response({'error': f'Parent not found: {parent_id}'}, status=status.HTTP_404_NOT_FOUND)
            else:
                doc.parent = None
            changes.append('parent')

        if changes:
            doc.save()
            return Response({
                'id': str(doc.id),
                'title': doc.title,
                'current_version': doc.current_version,
                'changes': changes,
                'message': f'Updated: {", ".join(changes)}',
            })
        else:
            return Response({'message': 'No changes specified'})

    def delete(self, request, pk):
        from django_agent_runtime.models import SpecDocument

        try:
            doc = SpecDocument.objects.get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        title = doc.title
        children_count = doc.children.count()
        doc.delete()

        return Response({
            'message': f'Deleted document: {title}',
            'deleted_children': children_count,
        })


class SpecDocumentLinkView(APIView):
    """Link or unlink a spec document to/from an agent."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django_agent_runtime.models import SpecDocument

        try:
            doc = SpecDocument.objects.get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        agent_id = request.data.get('agent_id')
        if not agent_id:
            return Response({'error': 'agent_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agent = AgentDefinition.objects.get(id=agent_id)
        except AgentDefinition.DoesNotExist:
            return Response({'error': f'Agent not found: {agent_id}'}, status=status.HTTP_404_NOT_FOUND)

        doc.linked_agent = agent
        doc.save()

        return Response({
            'message': f"Linked '{doc.title}' to agent '{agent.name}'",
            'document_id': str(doc.id),
            'agent_id': str(agent.id),
            'agent_slug': agent.slug,
        })

    def delete(self, request, pk):
        from django_agent_runtime.models import SpecDocument

        try:
            doc = SpecDocument.objects.select_related('linked_agent').get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        if not doc.linked_agent:
            return Response({'message': 'Document is not linked to any agent'})

        old_agent_name = doc.linked_agent.name
        doc.linked_agent = None
        doc.save()

        return Response({
            'message': f"Unlinked '{doc.title}' from agent '{old_agent_name}'",
            'document_id': str(doc.id),
        })


class SpecDocumentHistoryView(APIView):
    """Get version history of a spec document."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from django_agent_runtime.models import SpecDocument

        try:
            doc = SpecDocument.objects.get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        limit = int(request.query_params.get('limit', 20))
        versions = doc.versions.all()[:limit]

        return Response({
            'document_id': str(doc.id),
            'document_title': doc.title,
            'current_version': doc.current_version,
            'versions': [
                {
                    'version_number': v.version_number,
                    'title': v.title,
                    'content_preview': v.content[:200] + '...' if len(v.content) > 200 else v.content,
                    'created_at': v.created_at.isoformat(),
                    'change_summary': v.change_summary or '',
                }
                for v in versions
            ],
        })


class SpecDocumentRestoreView(APIView):
    """Restore a spec document to a previous version."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django_agent_runtime.models import SpecDocument, SpecDocumentVersion

        try:
            doc = SpecDocument.objects.get(id=pk)
        except SpecDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        version_number = request.data.get('version_number')
        if version_number is None:
            return Response({'error': 'version_number is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            version = doc.versions.get(version_number=version_number)
        except SpecDocumentVersion.DoesNotExist:
            return Response({'error': f'Version not found: {version_number}'}, status=status.HTTP_404_NOT_FOUND)

        version.restore()
        doc.refresh_from_db()

        return Response({
            'message': f'Restored document to version {version_number}',
            'document_id': str(doc.id),
            'restored_from_version': version_number,
            'new_version': doc.current_version,
        })


class SpecDocumentTreeView(APIView):
    """Get the full document tree structure."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django_agent_runtime.models import SpecDocument

        def build_tree(parent_id=None):
            if parent_id:
                docs = SpecDocument.objects.filter(parent_id=parent_id).select_related('linked_agent').order_by('order', 'title')
            else:
                docs = SpecDocument.objects.filter(parent__isnull=True).select_related('linked_agent').order_by('order', 'title')

            result = []
            for doc in docs:
                node = {
                    'id': str(doc.id),
                    'title': doc.title,
                    'has_content': bool(doc.content),
                    'order': doc.order,
                    'linked_agent': {
                        'id': str(doc.linked_agent.id),
                        'slug': doc.linked_agent.slug,
                        'name': doc.linked_agent.name,
                    } if doc.linked_agent else None,
                    'children': build_tree(doc.id),
                }
                result.append(node)
            return result

        tree = build_tree()
        return Response({'tree': tree})


class SpecDocumentRenderView(APIView):
    """Render all spec documents as a single markdown document."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django_agent_runtime.models import SpecDocument

        root_id = request.query_params.get('root_id')

        if root_id:
            try:
                doc = SpecDocument.objects.get(id=root_id)
                markdown = doc.render_tree_as_markdown()
                return Response({
                    'markdown': markdown,
                    'root_document': doc.title,
                })
            except SpecDocument.DoesNotExist:
                return Response({'error': f'Document not found: {root_id}'}, status=status.HTTP_404_NOT_FOUND)
        else:
            roots = SpecDocument.objects.filter(parent__isnull=True).order_by('order', 'title')
            parts = [root.render_tree_as_markdown() for root in roots]

            return Response({
                'markdown': '\n\n---\n\n'.join(parts),
                'root_count': len(parts),
                'roots': [{'id': str(r.id), 'title': r.title} for r in roots],
            })


class AgentSpecDocumentView(APIView):
    """Get or create the spec document linked to an agent."""
    permission_classes = [IsAuthenticated]

    def get(self, request, agent_id):
        """Get the spec document linked to this agent, or return empty if none exists."""
        from django_agent_runtime.models import SpecDocument

        agent = get_agent_for_user(request.user, agent_id)

        spec_doc = SpecDocument.objects.filter(linked_agent=agent).first()

        if spec_doc:
            return Response({
                'id': str(spec_doc.id),
                'title': spec_doc.title,
                'content': spec_doc.content,
                'current_version': spec_doc.current_version,
                'has_spec': bool(spec_doc.content),
                'created_at': spec_doc.created_at.isoformat(),
                'updated_at': spec_doc.updated_at.isoformat(),
            })
        else:
            return Response({
                'id': None,
                'title': None,
                'content': '',
                'current_version': 0,
                'has_spec': False,
            })

    def put(self, request, agent_id):
        """Update or create the spec document for this agent."""
        from django_agent_runtime.models import SpecDocument

        agent = get_agent_for_user(request.user, agent_id)
        content = request.data.get('content', '')

        spec_doc = SpecDocument.objects.filter(linked_agent=agent).first()

        if spec_doc:
            # Update existing
            spec_doc.content = content
            spec_doc.save()  # Auto-creates version
            created = False
        else:
            # Create new
            spec_doc = SpecDocument.objects.create(
                title=f"{agent.name} Specification",
                content=content,
                linked_agent=agent,
                owner=request.user if request.user.is_authenticated else None,
            )
            created = True

        return Response({
            'id': str(spec_doc.id),
            'title': spec_doc.title,
            'content': spec_doc.content,
            'current_version': spec_doc.current_version,
            'created': created,
            'message': f"Spec {'created' if created else 'updated'} for {agent.name}",
        })


# =============================================================================
# Collaborator Management Views
# =============================================================================

from django_agent_runtime.models import (
    AgentCollaborator,
    SystemCollaborator,
    CollaboratorRole,
)
from django_agent_studio.api.serializers import (
    AgentCollaboratorSerializer,
    SystemCollaboratorSerializer,
    AddCollaboratorSerializer,
    UpdateCollaboratorRoleSerializer,
)


class AgentCollaboratorListCreateView(generics.ListCreateAPIView):
    """
    List and add collaborators to an agent.

    GET /api/agents/{id}/collaborators/
    POST /api/agents/{id}/collaborators/

    Only owners and admins can manage collaborators.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCollaboratorSerializer
        return AgentCollaboratorSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs['agent_id'])
        return agent.collaborators.select_related('user', 'added_by').all()

    def create(self, request, *args, **kwargs):
        agent = get_agent_for_user(request.user, self.kwargs['agent_id'])

        # Check if user can manage collaborators (owner or admin)
        if not self._can_admin(request.user, agent):
            return Response(
                {'error': 'Only owners and admins can manage collaborators'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Find user by email or username
        from django.contrib.auth import get_user_model
        User = get_user_model()
        identifier = serializer.validated_data['email']

        # Try to find user by email first, then username
        user = None
        user_fields = [f.name for f in User._meta.get_fields()]

        if 'email' in user_fields:
            user = User.objects.filter(email=identifier).first()
        if not user and 'username' in user_fields:
            user = User.objects.filter(username=identifier).first()

        if not user:
            return Response(
                {'error': f"User '{identifier}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Can't add owner as collaborator
        if user == agent.owner:
            return Response(
                {'error': 'Cannot add the owner as a collaborator'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already a collaborator
        if AgentCollaborator.objects.filter(agent=agent, user=user).exists():
            return Response(
                {'error': 'User is already a collaborator on this agent'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create collaborator
        collaborator = AgentCollaborator.objects.create(
            agent=agent,
            user=user,
            role=serializer.validated_data.get('role', CollaboratorRole.VIEWER),
            added_by=request.user,
        )

        return Response(
            AgentCollaboratorSerializer(collaborator).data,
            status=status.HTTP_201_CREATED,
        )

    def _can_admin(self, user, agent):
        """Check if user can manage collaborators."""
        if user.is_superuser or agent.owner == user:
            return True
        try:
            collab = AgentCollaborator.objects.get(agent=agent, user=user)
            return collab.can_admin
        except AgentCollaborator.DoesNotExist:
            return False


class AgentCollaboratorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an agent collaborator.

    GET/PUT/PATCH/DELETE /api/agents/{id}/collaborators/{collaborator_id}/

    Only owners and admins can manage collaborators.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AgentCollaboratorSerializer

    def get_queryset(self):
        agent = get_agent_for_user(self.request.user, self.kwargs['agent_id'])
        return agent.collaborators.select_related('user', 'added_by').all()

    def update(self, request, *args, **kwargs):
        agent = get_agent_for_user(request.user, self.kwargs['agent_id'])

        if not self._can_admin(request.user, agent):
            return Response(
                {'error': 'Only owners and admins can manage collaborators'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Use the role update serializer for validation
        role_serializer = UpdateCollaboratorRoleSerializer(data=request.data)
        role_serializer.is_valid(raise_exception=True)

        collaborator = self.get_object()
        collaborator.role = role_serializer.validated_data['role']
        collaborator.save()

        return Response(AgentCollaboratorSerializer(collaborator).data)

    def destroy(self, request, *args, **kwargs):
        agent = get_agent_for_user(request.user, self.kwargs['agent_id'])

        if not self._can_admin(request.user, agent):
            return Response(
                {'error': 'Only owners and admins can manage collaborators'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    def _can_admin(self, user, agent):
        """Check if user can manage collaborators."""
        if user.is_superuser or agent.owner == user:
            return True
        try:
            collab = AgentCollaborator.objects.get(agent=agent, user=user)
            return collab.can_admin
        except AgentCollaborator.DoesNotExist:
            return False


class SystemCollaboratorListCreateView(generics.ListCreateAPIView):
    """
    List and add collaborators to a system.

    GET /api/systems/{id}/collaborators/
    POST /api/systems/{id}/collaborators/

    Only owners and admins can manage collaborators.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddCollaboratorSerializer
        return SystemCollaboratorSerializer

    def get_queryset(self):
        system = get_system_for_user(self.request.user, self.kwargs['system_id'])
        return system.collaborators.select_related('user', 'added_by').all()

    def create(self, request, *args, **kwargs):
        system = get_system_for_user(request.user, self.kwargs['system_id'])

        # Check if user can manage collaborators (owner or admin)
        if not self._can_admin(request.user, system):
            return Response(
                {'error': 'Only owners and admins can manage collaborators'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Find user by email or username
        from django.contrib.auth import get_user_model
        User = get_user_model()
        identifier = serializer.validated_data['email']

        # Try to find user by email first, then username
        user = None
        user_fields = [f.name for f in User._meta.get_fields()]

        if 'email' in user_fields:
            user = User.objects.filter(email=identifier).first()
        if not user and 'username' in user_fields:
            user = User.objects.filter(username=identifier).first()

        if not user:
            return Response(
                {'error': f"User '{identifier}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Can't add owner as collaborator
        if user == system.owner:
            return Response(
                {'error': 'Cannot add the owner as a collaborator'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already a collaborator
        if SystemCollaborator.objects.filter(system=system, user=user).exists():
            return Response(
                {'error': 'User is already a collaborator on this system'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create collaborator
        collaborator = SystemCollaborator.objects.create(
            system=system,
            user=user,
            role=serializer.validated_data.get('role', CollaboratorRole.VIEWER),
            added_by=request.user,
        )

        return Response(
            SystemCollaboratorSerializer(collaborator).data,
            status=status.HTTP_201_CREATED,
        )

    def _can_admin(self, user, system):
        """Check if user can manage collaborators."""
        if user.is_superuser or system.owner == user:
            return True
        try:
            collab = SystemCollaborator.objects.get(system=system, user=user)
            return collab.can_admin
        except SystemCollaborator.DoesNotExist:
            return False


class SystemCollaboratorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a system collaborator.

    GET/PUT/PATCH/DELETE /api/systems/{id}/collaborators/{collaborator_id}/

    Only owners and admins can manage collaborators.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SystemCollaboratorSerializer

    def get_queryset(self):
        system = get_system_for_user(self.request.user, self.kwargs['system_id'])
        return system.collaborators.select_related('user', 'added_by').all()

    def update(self, request, *args, **kwargs):
        system = get_system_for_user(request.user, self.kwargs['system_id'])

        if not self._can_admin(request.user, system):
            return Response(
                {'error': 'Only owners and admins can manage collaborators'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Use the role update serializer for validation
        role_serializer = UpdateCollaboratorRoleSerializer(data=request.data)
        role_serializer.is_valid(raise_exception=True)

        collaborator = self.get_object()
        collaborator.role = role_serializer.validated_data['role']
        collaborator.save()

        return Response(SystemCollaboratorSerializer(collaborator).data)

    def destroy(self, request, *args, **kwargs):
        system = get_system_for_user(request.user, self.kwargs['system_id'])

        if not self._can_admin(request.user, system):
            return Response(
                {'error': 'Only owners and admins can manage collaborators'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    def _can_admin(self, user, system):
        """Check if user can manage collaborators."""
        if user.is_superuser or system.owner == user:
            return True
        try:
            collab = SystemCollaborator.objects.get(system=system, user=user)
            return collab.can_admin
        except SystemCollaborator.DoesNotExist:
            return False


class UserSearchView(APIView):
    """
    Search for users by email, username, or name for collaborator autocomplete.

    GET /api/users/search/?q=<query>

    Returns up to 10 matching users.
    Handles both email-based and username-based User models.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from django.db.models import Q

        User = get_user_model()
        query = request.query_params.get('q', '').strip()

        if len(query) < 2:
            return Response([])

        # Build query filters based on available fields
        # Check which fields exist on the User model
        user_fields = [f.name for f in User._meta.get_fields()]

        filters = Q()
        if 'email' in user_fields:
            filters |= Q(email__icontains=query)
        if 'username' in user_fields:
            filters |= Q(username__icontains=query)
        if 'first_name' in user_fields:
            filters |= Q(first_name__icontains=query)
        if 'last_name' in user_fields:
            filters |= Q(last_name__icontains=query)
        if 'full_name' in user_fields:
            filters |= Q(full_name__icontains=query)

        users = User.objects.filter(filters).exclude(
            id=request.user.id  # Exclude current user
        )[:10]

        results = []
        for user in users:
            # Get identifier (email or username)
            identifier = getattr(user, 'email', None) or getattr(user, 'username', None) or str(user)

            # Get display name
            full_name = getattr(user, 'full_name', None) or ''
            first_name = getattr(user, 'first_name', None) or ''
            last_name = getattr(user, 'last_name', None) or ''
            name = full_name or f"{first_name} {last_name}".strip() or identifier

            # Build display string
            if name != identifier:
                display = f"{name} ({identifier})"
            else:
                display = identifier

            results.append({
                'id': str(user.id),
                'email': identifier,  # Keep as 'email' for backward compatibility
                'name': name,
                'display': display,
            })

        return Response(results)
