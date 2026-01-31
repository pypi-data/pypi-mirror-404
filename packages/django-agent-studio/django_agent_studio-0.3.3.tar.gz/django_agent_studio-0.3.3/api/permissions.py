"""
DRF Permission classes for Dynamic Tool access control.

These permissions integrate with the DynamicToolPermissionService
to enforce access levels on API endpoints.
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from django_agent_studio.services.permissions import get_permission_service


class BaseDynamicToolPermission(permissions.BasePermission):
    """
    Base class for dynamic tool permissions.
    
    Subclasses should set `required_level` to the minimum access level needed.
    """
    
    required_level: str = None
    message = "You do not have permission to perform this action."
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get agent from view kwargs if available
        agent = self._get_agent(request, view)
        
        service = get_permission_service()
        return service.has_level(request.user, self.required_level, agent)
    
    def _get_agent(self, request: Request, view: APIView):
        """Try to get the agent from the view."""
        from django_agent_runtime.models import AgentDefinition
        
        agent_id = view.kwargs.get('agent_id') or view.kwargs.get('pk')
        if agent_id:
            try:
                return AgentDefinition.objects.get(id=agent_id)
            except AgentDefinition.DoesNotExist:
                return None
        return None


class CanViewDynamicTools(BaseDynamicToolPermission):
    """Permission to view discovered functions and tools."""
    
    required_level = 'viewer'
    message = "You need at least Viewer access to view dynamic tools."


class CanScanProject(BaseDynamicToolPermission):
    """Permission to scan project for functions."""
    
    required_level = 'scanner'
    message = "You need at least Scanner access to scan the project."


class CanRequestTool(BaseDynamicToolPermission):
    """Permission to request tool creation (with approval)."""
    
    required_level = 'requester'
    message = "You need at least Requester access to request tool creation."


class CanCreateTool(BaseDynamicToolPermission):
    """Permission to create tools directly without approval."""
    
    required_level = 'creator'
    message = "You need Creator access to create tools directly."


class CanApproveTool(BaseDynamicToolPermission):
    """Permission to approve/reject tool requests."""
    
    required_level = 'admin'
    message = "You need Admin access to approve tool requests."


class CanManagePermissions(BaseDynamicToolPermission):
    """Permission to manage other users' access levels."""
    
    required_level = 'admin'
    message = "You need Admin access to manage permissions."


class DynamicToolObjectPermission(permissions.BasePermission):
    """
    Object-level permission for dynamic tools.
    
    Checks if user can modify/delete a specific tool.
    """
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        service = get_permission_service()
        
        # Read operations need viewer access
        if request.method in permissions.SAFE_METHODS:
            return service.can_view(request.user, obj.agent)
        
        # Delete needs admin
        if request.method == 'DELETE':
            return service.can_delete_tool(request.user, obj)
        
        # Modify needs creator
        return service.can_modify_tool(request.user, obj)


class IsOwnerOrHasDynamicToolAccess(permissions.BasePermission):
    """
    Combined permission: owner of agent OR has dynamic tool access.
    
    This allows the existing owner-based access to work alongside
    the new permission system.
    """
    
    required_level: str = 'viewer'
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
        
        # Check if user owns the agent
        from django_agent_runtime.models import AgentDefinition
        
        agent_id = view.kwargs.get('agent_id') or view.kwargs.get('pk')
        if agent_id:
            try:
                agent = AgentDefinition.objects.get(id=agent_id)
                if agent.owner == request.user:
                    return True
            except AgentDefinition.DoesNotExist:
                pass
        
        # Fall back to permission service
        service = get_permission_service()
        agent = self._get_agent(request, view)
        return service.has_level(request.user, self.required_level, agent)
    
    def _get_agent(self, request: Request, view: APIView):
        from django_agent_runtime.models import AgentDefinition
        
        agent_id = view.kwargs.get('agent_id') or view.kwargs.get('pk')
        if agent_id:
            try:
                return AgentDefinition.objects.get(id=agent_id)
            except AgentDefinition.DoesNotExist:
                return None
        return None

