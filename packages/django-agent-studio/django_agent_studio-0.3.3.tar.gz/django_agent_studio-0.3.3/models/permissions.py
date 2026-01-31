"""
Permission models for Dynamic Tool access control.

Provides:
- Access levels for dynamic tool operations
- Per-user access assignments
- Approval workflow for tool creation requests
"""

import uuid
from django.conf import settings
from django.db import models


class DynamicToolAccessLevel(models.TextChoices):
    """
    Access levels for dynamic tool operations.
    
    Ordered from least to most privileged:
    - NONE: No access to dynamic tools
    - VIEWER: Can view discovered functions and existing tools
    - SCANNER: Can scan project for functions
    - REQUESTER: Can request tool creation (needs admin approval)
    - CREATOR: Can create tools directly (no approval needed)
    - ADMIN: Full access including approving requests and managing permissions
    """
    NONE = 'none', 'No Access'
    VIEWER = 'viewer', 'Viewer (read-only)'
    SCANNER = 'scanner', 'Scanner (can scan project)'
    REQUESTER = 'requester', 'Requester (needs approval)'
    CREATOR = 'creator', 'Creator (can create tools)'
    ADMIN = 'admin', 'Admin (full access)'


# Define the hierarchy for permission checks
ACCESS_LEVEL_HIERARCHY = {
    DynamicToolAccessLevel.NONE: 0,
    DynamicToolAccessLevel.VIEWER: 1,
    DynamicToolAccessLevel.SCANNER: 2,
    DynamicToolAccessLevel.REQUESTER: 3,
    DynamicToolAccessLevel.CREATOR: 4,
    DynamicToolAccessLevel.ADMIN: 5,
}


class UserDynamicToolAccess(models.Model):
    """
    Per-user access level for dynamic tools.
    
    If a user doesn't have a record, they default to NONE access
    unless they're a superuser (who always have ADMIN access).
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dynamic_tool_access',
    )
    
    access_level = models.CharField(
        max_length=20,
        choices=DynamicToolAccessLevel.choices,
        default=DynamicToolAccessLevel.NONE,
    )
    
    # Optional: restrict to specific agents
    # If empty, access applies to all agents user can access
    restricted_to_agents = models.ManyToManyField(
        'django_agent_runtime.AgentDefinition',
        blank=True,
        related_name='dynamic_tool_access_grants',
        help_text='If set, access only applies to these agents',
    )
    
    # Audit fields
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dynamic_tool_access_grants_given',
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    notes = models.TextField(
        blank=True,
        help_text='Reason for granting this access level',
    )
    
    class Meta:
        verbose_name = 'User Dynamic Tool Access'
        verbose_name_plural = 'User Dynamic Tool Access'
    
    def __str__(self):
        return f"{self.user} - {self.get_access_level_display()}"
    
    def has_level(self, required_level: str) -> bool:
        """Check if user has at least the required access level."""
        user_rank = ACCESS_LEVEL_HIERARCHY.get(self.access_level, 0)
        required_rank = ACCESS_LEVEL_HIERARCHY.get(required_level, 0)
        return user_rank >= required_rank


class ToolApprovalRequest(models.Model):
    """
    Request for tool creation that requires admin approval.
    
    Created when a user with REQUESTER access level wants to create a tool.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled by Requester'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The agent this tool would be added to
    agent = models.ForeignKey(
        'django_agent_runtime.AgentDefinition',
        on_delete=models.CASCADE,
        related_name='tool_approval_requests',
    )
    
    # The discovered function to convert to a tool
    discovered_function = models.ForeignKey(
        'django_agent_runtime.DiscoveredFunction',
        on_delete=models.CASCADE,
        related_name='approval_requests',
    )
    
    # Requester's proposed configuration
    proposed_name = models.CharField(max_length=100)
    proposed_description = models.TextField()
    proposed_is_safe = models.BooleanField(default=False)
    proposed_requires_confirmation = models.BooleanField(default=True)
    proposed_timeout_seconds = models.PositiveIntegerField(default=30)
    
    # Request metadata
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tool_approval_requests',
    )
    request_reason = models.TextField(
        help_text='Why this tool is needed',
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    
    # Review metadata
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tool_approval_reviews',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # If approved, link to the created tool
    created_tool = models.ForeignKey(
        'django_agent_runtime.DynamicTool',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_request',
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tool Approval Request'
        verbose_name_plural = 'Tool Approval Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.proposed_name} - {self.get_status_display()}"

