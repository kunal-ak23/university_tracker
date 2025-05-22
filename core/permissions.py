from rest_framework import permissions

class IsAdminOrAgent(permissions.BasePermission):
    """
    Custom permission to only allow admin users and agents to access the view.
    """
    def has_permission(self, request, view):
        # Allow admin users and agents
        return request.user.is_superuser or request.user.is_agent()

class IsAuthenticatedAndReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users to read.
    """
    def has_permission(self, request, view):
        # Allow read-only access for authenticated users
        return request.user.is_authenticated and request.method in permissions.SAFE_METHODS