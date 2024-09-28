from rest_framework.permissions import BasePermission

class IsProviderPOC(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'provider_poc' or request.user.role == 'admin')

class IsUniversityPOC(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'university_poc' or request.user.role == 'admin')