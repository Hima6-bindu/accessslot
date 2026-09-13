"""
API views for Equipment management.
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Equipment
from .serializers import (
    EquipmentSerializer,
    EquipmentListSerializer,
    EquipmentDetailSerializer
)
from users.permissions import IsAdmin


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Equipment CRUD operations.
    
    Permissions:
    - List/Retrieve: Any authenticated user
    - Create/Update/Delete: Admin only
    
    GET    /api/equipment/           - List all equipment
    POST   /api/equipment/           - Create equipment (admin only)
    GET    /api/equipment/{id}/      - Retrieve equipment details
    PUT    /api/equipment/{id}/      - Update equipment (admin only)
    PATCH  /api/equipment/{id}/      - Partial update (admin only)
    DELETE /api/equipment/{id}/      - Delete equipment (admin only)
    """
    
    queryset = Equipment.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'equipment_type', 'location']
    search_fields = ['name', 'description', 'equipment_type', 'location']
    ordering_fields = ['name', 'equipment_type', 'created_at', 'status']
    ordering = ['name']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return EquipmentListSerializer
        elif self.action == 'retrieve':
            return EquipmentDetailSerializer
        return EquipmentSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action.
        - list, retrieve: IsAuthenticated
        - create, update, partial_update, destroy: IsAdmin
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]
    
    def list(self, request, *args, **kwargs):
        """
        List all equipment with optional filtering.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create new equipment (admin only).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                'message': 'Equipment created successfully',
                'equipment': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve equipment details.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update equipment (admin only).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(
            {
                'message': 'Equipment updated successfully',
                'equipment': serializer.data
            }
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete equipment (admin only).
        """
        instance = self.get_object()
        equipment_name = instance.name
        self.perform_destroy(instance)
        
        return Response(
            {
                'message': f'Equipment "{equipment_name}" deleted successfully'
            },
            status=status.HTTP_200_OK
        )
