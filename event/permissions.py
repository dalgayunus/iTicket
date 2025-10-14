from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated


class IsAdminOrReadOnly(IsAuthenticated):

    def has_permission(self, request, view):
        super().has_permission(request, view)

        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_authenticated and request.user.role == 'admin'


class IsOrganizerOrAdmin(IsAuthenticated):

    def has_permission(self, request, view):
        super().has_permission(request, view)
        if not request.user.is_authenticated:
            return False
        
        return request.user.role in ['organizer', 'admin']


class IsCustomerOrAdmin(IsAuthenticated):

    def has_permission(self, request, view):
        super().has_permission(request, view)
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['customer', 'admin']


class IsOwnerOrAdmin(IsAuthenticated):
    
    def has_object_permission(self, request, view, obj):
        super().has_object_permission(request, view, obj)
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_authenticated and (
            request.user.role == 'admin' or 
            hasattr(obj, 'user') and obj.user == request.user
        )


class CanManageEvents(IsAuthenticated):
    
    def has_permission(self, request, view):
        super().has_permission(request, view)
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
        
        elif request.user.role == 'organizer':
            return request.method in ['GET', 'POST', 'PUT', 'PATCH']
        
        elif request.user.role == 'customer':
            return request.method in permissions.SAFE_METHODS
        
        return False


class CanApplyDiscount(IsAuthenticated):
    
    def has_permission(self, request, view):
        super().has_permission(request, view)
        if not request.user.is_authenticated:
            return False
        
        return request.user.role in ['organizer', 'admin']


class CanManageTickets(IsAuthenticated):

    def has_permission(self, request, view):
        super().has_permission(request, view)
        
        if not request.user.is_authenticated:
            return False

        if request.user.role == 'admin':
            return True

        elif request.user.role == 'organizer':
            return request.method in ['GET', 'POST', 'PUT', 'PATCH']

        elif request.user.role == 'customer':
            return False
        
        return False


class CanManageCategories(IsAuthenticated):

    def has_permission(self, request, view):
        super().has_permission(request, view)
        if not request.user.is_authenticated:
            return False
        
        return request.user.role == 'admin'