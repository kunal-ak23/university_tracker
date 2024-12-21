from rest_framework import permissions

class IsAuthenticatedAndReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow any authenticated user to read
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
            
        # For write operations, require superuser or specific roles
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.is_provider_poc() or 
            request.user.is_university_poc()
        )