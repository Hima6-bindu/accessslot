"""
Admin-specific views for user management.
Only accessible to ADMIN role users.
"""
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db.models import Q

from .permissions import IsAdmin
from .admin_serializers import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer
)

User = get_user_model()


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin user management.
    
    Only ADMIN users can access these endpoints.
    
    GET    /api/users/            - List all users
    GET    /api/users/{id}/       - Get user details
    PATCH  /api/users/{id}/       - Update user
    
    Security:
    - Never returns passwords, password hashes, or JWT tokens
    - Only accessible to ADMIN role
    - Prevents deactivating the last admin
    """
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return AdminUserListSerializer
        elif self.action == 'retrieve':
            return AdminUserDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        return AdminUserListSerializer
    
    def get_queryset(self):
        """
        Optionally filter users based on query parameters.
        """
        queryset = User.objects.all().order_by('-date_joined')
        
        # Search by username, email, first name, or last name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        List all users with optional filtering.
        
        Query Parameters:
        - search: Search by username, email, or name
        - role: Filter by role (STUDENT, FACULTY, ADMIN)
        - is_active: Filter by active status (true/false)
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Use pagination if configured
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get detailed information about a specific user.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update a user's information.
        
        Allows updating: first_name, last_name, email, role, is_active
        
        Protections:
        - Cannot deactivate the last active admin
        - Cannot remove admin role from the last active admin
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return detailed user info after update
        detail_serializer = AdminUserDetailSerializer(instance)
        
        return Response({
            'message': 'User updated successfully',
            'user': detail_serializer.data
        })
    
    def perform_update(self, serializer):
        """
        Perform the update.
        """
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Disable DELETE method.
        
        Users should be deactivated, not deleted, to preserve data integrity.
        """
        return Response(
            {'detail': 'Deleting users is not allowed. Use is_active=false to deactivate.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
