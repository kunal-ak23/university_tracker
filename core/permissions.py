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

class IsAuthenticatedWithRoleBasedAccess(permissions.BasePermission):
    """
    Custom permission that allows authenticated users to perform CRUD operations
    based on their role and the resource they're accessing.
    """
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Superusers can do everything
        if request.user.is_superuser:
            return True
        
        # For read operations, allow all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, check role-based permissions
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # University POC can create/update universities and related resources
            if request.user.is_university_poc():
                return True
            
            # Provider POC can create/update OEMs and related resources
            if request.user.is_provider_poc():
                return True
            
            # Agents can create/update leads
            if request.user.is_agent():
                return True
        
        return False

    def has_object_permission(self, request, view, obj):
        # Superusers can do everything
        if request.user.is_superuser:
            return True
        
        # For read operations, allow all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, check object-level permissions
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # University POC can update their own universities
            if hasattr(obj, 'poc') and obj.poc == request.user:
                return True
            
            # Provider POC can update their own OEMs
            if hasattr(obj, 'poc') and obj.poc == request.user:
                return True
            
            # Check if user is related to the object through other means
            # This handles cases like batch updates for university POCs
            if hasattr(obj, 'university') and hasattr(obj.university, 'poc'):
                if obj.university.poc == request.user:
                    return True
            
            if hasattr(obj, 'oem') and hasattr(obj.oem, 'poc'):
                if obj.oem.poc == request.user:
                    return True
        
        return False