"""
API views for Maintenance management.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from users.permissions import IsAdmin
from .models import Maintenance
from .maintenance_serializers import (
    MaintenanceSerializer,
    MaintenanceCreateSerializer,
    MaintenanceUpdateSerializer
)
from .maintenance_services import MaintenanceService


class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing equipment maintenance records.
    
    - List: All authenticated users can view maintenance schedules
    - Create: Admin only
    - Update: Admin only
    - Delete: Admin only
    """
    queryset = Maintenance.objects.all().select_related('equipment', 'created_by')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['equipment', 'equipment__equipment_type']
    ordering_fields = ['start_time', 'end_time', 'created_at']
    ordering = ['-start_time']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return MaintenanceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MaintenanceUpdateSerializer
        return MaintenanceSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action.
        - List/Retrieve: Any authenticated user
        - Create/Update/Delete: Admin only
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Create a new maintenance record.
        Uses MaintenanceService to handle overlap validation and conflict detection.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use the service layer to create maintenance with proper validation
        maintenance = MaintenanceService.create_maintenance(
            equipment=serializer.validated_data['equipment'],
            start_time=serializer.validated_data['start_time'],
            end_time=serializer.validated_data['end_time'],
            reason=serializer.validated_data['reason'],
            created_by=request.user
        )
        
        # Return the created maintenance with full serialization
        output_serializer = MaintenanceSerializer(maintenance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update a maintenance record.
        Uses MaintenanceService to handle validation.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Use the service layer to update with proper validation
        maintenance = MaintenanceService.update_maintenance(
            maintenance_id=instance.id,
            start_time=serializer.validated_data.get('start_time'),
            end_time=serializer.validated_data.get('end_time'),
            reason=serializer.validated_data.get('reason')
        )
        
        # Return the updated maintenance
        output_serializer = MaintenanceSerializer(maintenance)
        return Response(output_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a maintenance record.
        Only admins can delete maintenance records.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
