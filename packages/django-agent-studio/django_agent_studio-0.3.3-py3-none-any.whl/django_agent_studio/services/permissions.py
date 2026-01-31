"""
Permission service for Dynamic Tool access control.

Provides centralized permission checking for all dynamic tool operations.
"""

import logging
from typing import Optional, TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from django_agent_studio.models.permissions import (
    DynamicToolAccessLevel,
    UserDynamicToolAccess,
    ToolApprovalRequest,
    ACCESS_LEVEL_HIERARCHY,
)

if TYPE_CHECKING:
    from django_agent_runtime.models import AgentDefinition, DynamicTool

logger = logging.getLogger(__name__)
User = get_user_model()


class DynamicToolPermissionService:
    """
    Service for checking and managing dynamic tool permissions.
    
    Usage:
        service = DynamicToolPermissionService()
        
        # Check if user can scan
        if service.can_scan(user, agent):
            # do scan
        
        # Check if user can create tools directly or needs approval
        if service.can_create_tool(user, agent):
            # create directly
        elif service.can_request_tool(user, agent):
            # create approval request
    """
    
    def get_user_access_level(
        self,
        user,
        agent: Optional['AgentDefinition'] = None,
    ) -> str:
        """
        Get the effective access level for a user.
        
        Args:
            user: The user to check
            agent: Optional agent to check agent-specific restrictions
            
        Returns:
            The access level string
        """
        # Superusers always have admin access
        if user.is_superuser:
            return DynamicToolAccessLevel.ADMIN
        
        # Check for user-specific access
        try:
            access = UserDynamicToolAccess.objects.get(user=user)
            
            # If restricted to specific agents, check if this agent is included
            if agent and access.restricted_to_agents.exists():
                if not access.restricted_to_agents.filter(id=agent.id).exists():
                    return DynamicToolAccessLevel.NONE
            
            return access.access_level
        except UserDynamicToolAccess.DoesNotExist:
            return DynamicToolAccessLevel.NONE
    
    def has_level(
        self,
        user,
        required_level: str,
        agent: Optional['AgentDefinition'] = None,
    ) -> bool:
        """
        Check if user has at least the required access level.
        
        Args:
            user: The user to check
            required_level: The minimum required level
            agent: Optional agent for agent-specific checks
            
        Returns:
            True if user has sufficient access
        """
        user_level = self.get_user_access_level(user, agent)
        user_rank = ACCESS_LEVEL_HIERARCHY.get(user_level, 0)
        required_rank = ACCESS_LEVEL_HIERARCHY.get(required_level, 0)
        return user_rank >= required_rank
    
    # Convenience methods for specific operations
    
    def can_view(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user view discovered functions and tools?"""
        return self.has_level(user, DynamicToolAccessLevel.VIEWER, agent)
    
    def can_scan(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user scan project for functions?"""
        return self.has_level(user, DynamicToolAccessLevel.SCANNER, agent)
    
    def can_request_tool(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user request tool creation (with approval)?"""
        return self.has_level(user, DynamicToolAccessLevel.REQUESTER, agent)
    
    def can_create_tool(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user create tools directly without approval?"""
        return self.has_level(user, DynamicToolAccessLevel.CREATOR, agent)
    
    def can_approve(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user approve/reject tool requests?"""
        return self.has_level(user, DynamicToolAccessLevel.ADMIN, agent)
    
    def can_manage_permissions(self, user) -> bool:
        """Can user manage other users' access levels?"""
        return self.has_level(user, DynamicToolAccessLevel.ADMIN)
    
    def can_modify_tool(
        self,
        user,
        tool: 'DynamicTool',
    ) -> bool:
        """Can user modify an existing tool?"""
        return self.has_level(user, DynamicToolAccessLevel.CREATOR, tool.agent)
    
    def can_delete_tool(
        self,
        user,
        tool: 'DynamicTool',
    ) -> bool:
        """Can user delete a tool?"""
        return self.has_level(user, DynamicToolAccessLevel.ADMIN, tool.agent)

    # Multi-agent specific permissions

    def can_add_sub_agent(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user add sub-agent tools to an agent?"""
        return self.has_level(user, DynamicToolAccessLevel.CREATOR, agent)

    def can_remove_sub_agent(self, user, agent: Optional['AgentDefinition'] = None) -> bool:
        """Can user remove sub-agent tools from an agent?"""
        return self.has_level(user, DynamicToolAccessLevel.CREATOR, agent)

    def can_create_agent_system(self, user) -> bool:
        """Can user create multi-agent systems?"""
        return self.has_level(user, DynamicToolAccessLevel.CREATOR)

    def can_publish_system_version(self, user) -> bool:
        """Can user publish agent system versions?"""
        return self.has_level(user, DynamicToolAccessLevel.ADMIN)

    def can_deploy_system_version(self, user) -> bool:
        """Can user deploy (activate) agent system versions?"""
        return self.has_level(user, DynamicToolAccessLevel.ADMIN)

    # Access management methods
    
    def grant_access(
        self,
        user,
        access_level: str,
        granted_by,
        agents: Optional[QuerySet] = None,
        notes: str = '',
    ) -> UserDynamicToolAccess:
        """
        Grant or update access level for a user.
        
        Args:
            user: User to grant access to
            access_level: The access level to grant
            granted_by: User granting the access
            agents: Optional queryset of agents to restrict access to
            notes: Optional notes about why access was granted
            
        Returns:
            The created/updated access record
        """
        access, created = UserDynamicToolAccess.objects.update_or_create(
            user=user,
            defaults={
                'access_level': access_level,
                'granted_by': granted_by,
                'notes': notes,
            }
        )
        
        if agents is not None:
            access.restricted_to_agents.set(agents)
        
        action = 'Granted' if created else 'Updated'
        logger.info(
            f"{action} {access_level} access to {user} by {granted_by}"
        )
        
        return access
    
    def revoke_access(self, user) -> bool:
        """
        Revoke all dynamic tool access for a user.
        
        Returns:
            True if access was revoked, False if user had no access
        """
        deleted, _ = UserDynamicToolAccess.objects.filter(user=user).delete()
        if deleted:
            logger.info(f"Revoked dynamic tool access for {user}")
        return deleted > 0


# Singleton instance
_permission_service: Optional[DynamicToolPermissionService] = None


def get_permission_service() -> DynamicToolPermissionService:
    """Get the singleton permission service instance."""
    global _permission_service
    if _permission_service is None:
        _permission_service = DynamicToolPermissionService()
    return _permission_service

