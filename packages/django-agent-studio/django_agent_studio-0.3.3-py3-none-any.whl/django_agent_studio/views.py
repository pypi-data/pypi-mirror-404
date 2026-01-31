"""
Views for django_agent_studio.
"""

from django.contrib.auth import logout
from django.db.models import Q
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from django_agent_runtime.models import (
    AgentDefinition,
    AgentSystem,
    AgentSystemMember,
    AgentCollaborator,
    SystemCollaborator,
    CollaboratorRole,
)


class AgentAccessMixin:
    """
    Mixin that provides consistent agent access logic.

    - Superusers can access all agents
    - Owners can access their own agents
    - Collaborators can access agents they've been granted access to
    - Users with system access can access agents in that system
    """

    def get_user_agents_queryset(self):
        """Get queryset of agents accessible to the current user."""
        if self.request.user.is_superuser:
            return AgentDefinition.objects.all()

        user = self.request.user

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

    def get_agent_for_user(self, agent_id, require_edit=False):
        """
        Get a specific agent if the user has access.

        Args:
            agent_id: The agent's ID
            require_edit: If True, requires edit permission (editor or admin role)

        Returns:
            AgentDefinition if user has access

        Raises:
            AgentDefinition.DoesNotExist if no access
        """
        if self.request.user.is_superuser:
            return AgentDefinition.objects.get(id=agent_id)

        agent = AgentDefinition.objects.get(id=agent_id)
        user = self.request.user

        # Owner always has full access
        if agent.owner == user:
            return agent

        # Check direct collaborator access
        try:
            collab = AgentCollaborator.objects.get(agent=agent, user=user)
            if require_edit and not collab.can_edit:
                raise AgentDefinition.DoesNotExist("Edit permission required")
            return agent
        except AgentCollaborator.DoesNotExist:
            pass

        # Check if user has access via a system that contains this agent
        agent_system_ids = AgentSystemMember.objects.filter(
            agent=agent
        ).values_list('system_id', flat=True)

        if agent_system_ids:
            # Check for system owner or collaborator access
            system_collab = SystemCollaborator.objects.filter(
                system_id__in=agent_system_ids, user=user
            ).first()
            if system_collab:
                if require_edit and not system_collab.can_edit:
                    raise AgentDefinition.DoesNotExist("Edit permission required")
                return agent

            # Check if user owns any of these systems
            if AgentSystem.objects.filter(id__in=agent_system_ids, owner=user).exists():
                return agent

        raise AgentDefinition.DoesNotExist("No access to this agent")

    def get_agent_role(self, agent):
        """
        Get the user's role for an agent.

        Returns:
            'owner', 'admin', 'editor', 'viewer', or None
            Also returns tuple (role, source) where source is 'direct' or 'system:<name>'
        """
        user = self.request.user
        if user.is_superuser or agent.owner == user:
            return 'owner'

        # Check direct collaborator
        try:
            collab = AgentCollaborator.objects.get(agent=agent, user=user)
            return collab.role
        except AgentCollaborator.DoesNotExist:
            pass

        # Check system-level access
        agent_systems = AgentSystemMember.objects.filter(
            agent=agent
        ).select_related('system')

        for member in agent_systems:
            system = member.system
            if system.owner == user:
                return 'owner'
            try:
                sys_collab = SystemCollaborator.objects.get(system=system, user=user)
                return sys_collab.role
            except SystemCollaborator.DoesNotExist:
                continue

        return None

    def get_agent_access_info(self, agent):
        """
        Get detailed access info for an agent.

        Returns dict with:
            - role: 'owner', 'admin', 'editor', 'viewer', or None
            - source: 'direct', 'system', or None
            - system_name: Name of system granting access (if source is 'system')
        """
        user = self.request.user
        if user.is_superuser or agent.owner == user:
            return {'role': 'owner', 'source': 'direct', 'system_name': None}

        # Check direct collaborator
        try:
            collab = AgentCollaborator.objects.get(agent=agent, user=user)
            return {'role': collab.role, 'source': 'direct', 'system_name': None}
        except AgentCollaborator.DoesNotExist:
            pass

        # Check system-level access
        agent_systems = AgentSystemMember.objects.filter(
            agent=agent
        ).select_related('system')

        for member in agent_systems:
            system = member.system
            if system.owner == user:
                return {'role': 'owner', 'source': 'system', 'system_name': system.name}
            try:
                sys_collab = SystemCollaborator.objects.get(system=system, user=user)
                return {'role': sys_collab.role, 'source': 'system', 'system_name': system.name}
            except SystemCollaborator.DoesNotExist:
                continue

        return {'role': None, 'source': None, 'system_name': None}

    def can_edit_agent(self, agent):
        """Check if user can edit the agent."""
        role = self.get_agent_role(agent)
        return role in ['owner', 'admin', 'editor']

    def can_admin_agent(self, agent):
        """Check if user can manage collaborators on the agent."""
        role = self.get_agent_role(agent)
        return role in ['owner', 'admin']


class SystemAccessMixin:
    """
    Mixin that provides consistent system access logic.

    - Superusers can access all systems
    - Owners can access their own systems
    - Collaborators can access systems they've been granted access to
    """

    def get_user_systems_queryset(self):
        """Get queryset of systems accessible to the current user."""
        if self.request.user.is_superuser:
            return AgentSystem.objects.all()
        # Include owned systems and systems where user is a collaborator
        return AgentSystem.objects.filter(
            Q(owner=self.request.user) |
            Q(collaborators__user=self.request.user)
        ).distinct()

    def get_system_for_user(self, system_id, require_edit=False):
        """
        Get a specific system if the user has access.

        Args:
            system_id: The system's ID
            require_edit: If True, requires edit permission (editor or admin role)

        Returns:
            AgentSystem if user has access

        Raises:
            AgentSystem.DoesNotExist if no access
        """
        if self.request.user.is_superuser:
            return AgentSystem.objects.select_related('entry_agent').get(id=system_id)

        system = AgentSystem.objects.select_related('entry_agent').get(id=system_id)

        # Owner always has full access
        if system.owner == self.request.user:
            return system

        # Check collaborator access
        try:
            collab = SystemCollaborator.objects.get(system=system, user=self.request.user)
            if require_edit and not collab.can_edit:
                raise AgentSystem.DoesNotExist("Edit permission required")
            return system
        except SystemCollaborator.DoesNotExist:
            raise AgentSystem.DoesNotExist("No access to this system")

    def get_system_role(self, system):
        """
        Get the user's role for a system.

        Returns:
            'owner', 'admin', 'editor', 'viewer', or None
        """
        if self.request.user.is_superuser or system.owner == self.request.user:
            return 'owner'
        try:
            collab = SystemCollaborator.objects.get(system=system, user=self.request.user)
            return collab.role
        except SystemCollaborator.DoesNotExist:
            return None

    def can_edit_system(self, system):
        """Check if user can edit the system."""
        role = self.get_system_role(system)
        return role in ['owner', 'admin', 'editor']

    def can_admin_system(self, system):
        """Check if user can manage collaborators on the system."""
        role = self.get_system_role(system)
        return role in ['owner', 'admin']


class StudioHomeView(LoginRequiredMixin, AgentAccessMixin, SystemAccessMixin, TemplateView):
    """Home page for the agent studio."""

    template_name = "django_agent_studio/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Systems (shown above agents)
        context["recent_systems"] = self.get_user_systems_queryset().select_related(
            'entry_agent'
        ).order_by("-updated_at")[:5]
        # Agents
        context["recent_agents"] = self.get_user_agents_queryset().order_by("-updated_at")[:5]
        context["template_agents"] = AgentDefinition.objects.filter(
            is_template=True,
            is_public=True,
        ).order_by("-updated_at")[:10]
        return context


class AgentListView(LoginRequiredMixin, AgentAccessMixin, ListView):
    """List all agents for the current user."""

    template_name = "django_agent_studio/agent_list.html"
    context_object_name = "agents"

    def get_queryset(self):
        return self.get_user_agents_queryset().order_by("-updated_at")


class AgentBuilderView(LoginRequiredMixin, AgentAccessMixin, TemplateView):
    """
    Two-pane agent builder interface.

    Left pane: Test the agent (agent-frontend instance)
    Right pane: Builder agent conversation (agent-frontend instance)
    """

    template_name = "django_agent_studio/builder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent_id = kwargs.get("agent_id")

        if agent_id:
            context["agent"] = self.get_agent_for_user(agent_id)
            context["is_new"] = False
        else:
            context["agent"] = None
            context["is_new"] = True

        # Configuration for the builder agent
        context["builder_agent_key"] = "agent-builder"

        return context


class AgentTestView(LoginRequiredMixin, AgentAccessMixin, TemplateView):
    """Full-screen agent testing interface."""

    template_name = "django_agent_studio/test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent_id = kwargs.get("agent_id")
        context["agent"] = self.get_agent_for_user(agent_id)
        return context


class SystemListView(LoginRequiredMixin, SystemAccessMixin, ListView):
    """List all systems for the current user."""

    template_name = "django_agent_studio/system_list.html"
    context_object_name = "systems"

    def get_queryset(self):
        return self.get_user_systems_queryset().select_related(
            'entry_agent'
        ).prefetch_related('members__agent').order_by("-updated_at")


class SystemCreateView(LoginRequiredMixin, AgentAccessMixin, TemplateView):
    """Create a new multi-agent system."""

    template_name = "django_agent_studio/system_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get user's agents for the entry agent dropdown
        context["agents"] = self.get_user_agents_queryset().order_by("name")
        return context


class SystemTestView(LoginRequiredMixin, SystemAccessMixin, TemplateView):
    """
    Full-screen system testing interface.

    Uses the system's entry_agent as the starting point for conversations.
    """

    template_name = "django_agent_studio/system_test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_id = kwargs.get("system_id")
        system = self.get_system_for_user(system_id)
        context["system"] = system
        context["agent"] = system.entry_agent  # The entry point agent
        return context


class AgentCollaboratorsView(LoginRequiredMixin, AgentAccessMixin, TemplateView):
    """Manage collaborators for an agent."""

    template_name = "django_agent_studio/collaborators.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent_id = kwargs.get("agent_id")
        agent = self.get_agent_for_user(agent_id)

        context["object"] = agent
        context["object_name"] = agent.name
        context["object_type"] = "agent"
        context["can_admin"] = self.can_admin_agent(agent)

        # Owner info
        if agent.owner:
            context["owner_email"] = agent.owner.email
            context["owner_initial"] = agent.owner.email[0].upper() if agent.owner.email else "?"
        else:
            context["owner_email"] = "No owner"
            context["owner_initial"] = "?"

        # Get systems this agent belongs to (for showing inherited access info)
        agent_systems = AgentSystemMember.objects.filter(
            agent=agent
        ).select_related('system', 'system__owner')
        context["parent_systems"] = [
            {
                'id': str(member.system.id),
                'name': member.system.name,
                'role': member.role,
            }
            for member in agent_systems
        ]

        return context


class SystemCollaboratorsView(LoginRequiredMixin, SystemAccessMixin, TemplateView):
    """Manage collaborators for a system."""

    template_name = "django_agent_studio/collaborators.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_id = kwargs.get("system_id")
        system = self.get_system_for_user(system_id)

        context["object"] = system
        context["object_name"] = system.name
        context["object_type"] = "system"
        context["can_admin"] = self.can_admin_system(system)

        # Owner info
        if system.owner:
            context["owner_email"] = system.owner.email
            context["owner_initial"] = system.owner.email[0].upper() if system.owner.email else "?"
        else:
            context["owner_email"] = "No owner"
            context["owner_initial"] = "?"

        # Get agents in this system (for showing what agents are included)
        system_members = AgentSystemMember.objects.filter(
            system=system
        ).select_related('agent')
        context["member_agents"] = [
            {
                'id': str(member.agent.id),
                'name': member.agent.name,
                'role': member.role,
            }
            for member in system_members
        ]

        return context


class LogoutView(View):
    """Simple logout view that works with any auth backend."""

    def post(self, request):
        logout(request)
        return redirect('/')

