"""
Custom permission classes for role-based access control.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class to allow access only to users with ADMIN role.
    """
    message = "You must be an admin to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has admin role.
        """
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsFaculty(permissions.BasePermission):
    """
    Permission class to allow access only to users with FACULTY role.
    """
    message = "You must be a faculty member to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has faculty role.
        """
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'FACULTY'
        )


class IsFacultyOrAdmin(permissions.BasePermission):
    """
    Permission class to allow access to FACULTY or ADMIN users.
    """
    message = "You must be a faculty member or admin to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has faculty or admin role.
        """
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['FACULTY', 'ADMIN']
        )


class IsStudent(permissions.BasePermission):
    """
    Permission class to allow access only to users with STUDENT role.
    """
    message = "You must be a student to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has student role.
        """
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'STUDENT'
        )


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has a `user` attribute.
    """
    message = "You can only access your own resources."
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user is the owner of the object.
        """
        # Allow admins to access all objects
        if request.user.role == 'ADMIN':
            return True
        
        # Check if object has a user attribute and matches the requesting user
        return hasattr(obj, 'user') and obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to allow owners or admins to access an object.
    """
    message = "You can only access your own resources or you must be an admin."
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user is the owner or an admin.
        """
        # Allow admins
        if request.user.role == 'ADMIN':
            return True
        
        # Allow owners
        return hasattr(obj, 'user') and obj.user == request.user


class ReadOnly(permissions.BasePermission):
    """
    Permission class to allow read-only access (GET, HEAD, OPTIONS).
    """
    message = "This endpoint is read-only."
    
    def has_permission(self, request, view):
        """
        Allow only safe methods (GET, HEAD, OPTIONS).
        """
        return request.method in permissions.SAFE_METHODS


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow read access to all users,
    but write access only to admins.
    """
    message = "You must be an admin to modify this resource."
    
    def has_permission(self, request, view):
        """
        Allow read operations for all authenticated users,
        write operations only for admins.
        """
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )
