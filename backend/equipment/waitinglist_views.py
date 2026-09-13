"""
API views for WaitingList management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from users.permissions import IsAdmin
from .models import WaitingList
from .waitinglist_serializers import (
    WaitingListSerializer,
    WaitingListJoinSerializer,
    WaitingListCancelSerializer
)
from .waitinglist_services import WaitingListService


class WaitingListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing waiting list entries.
    
    - List: Users see their own entries, admins see all
    - Create (join): Any authenticated user
    - Cancel: Users can cancel their own entries, admins can cancel any
    - Admin management: Admins can view and manage all entries
    """
    serializer_class = WaitingListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['equipment', 'status', 'user']
    ordering_fields = ['position', 'created_at', 'requested_start_time']
    ordering = ['equipment', 'position', 'created_at']
    
    def get_queryset(self):
        """
        Return queryset based on user role.
        - Regular users: Only their own entries
        - Admins: All entries
        """
        user = self.request.user
        
        if user.role == 'ADMIN':
            return WaitingList.objects.all().select_related('user', 'equipment')
        else:
            return WaitingList.objects.filter(user=user).select_related('equipment')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'join':
            return WaitingListJoinSerializer
        elif self.action == 'cancel_entry':
            return WaitingListCancelSerializer
        return WaitingListSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Not used - use the 'join' action instead.
        """
        return Response(
            {'detail': 'Use POST /api/waiting-list/join/ to join the waiting list.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def update(self, request, *args, **kwargs):
        """
        Not allowed - waiting list entries cannot be updated directly.
        """
        return Response(
            {'detail': 'Waiting list entries cannot be updated. Cancel and create a new entry if needed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Not used - use the 'cancel_entry' action instead.
        """
        return Response(
            {'detail': 'Use POST /api/waiting-list/{id}/cancel/ to cancel an entry.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'], url_path='join')
    def join(self, request):
        """
        Join the waiting list for an equipment.
        Creates a new waiting list entry with proper FIFO position.
        """
        serializer = WaitingListJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use the service layer to join with proper FIFO and concurrency protection
        entry = WaitingListService.join_waiting_list(
            user=request.user,
            equipment=serializer.validated_data['equipment'],
            requested_start_time=serializer.validated_data['requested_start_time'],
            requested_end_time=serializer.validated_data['requested_end_time']
        )
        
        # Return the created entry
        output_serializer = WaitingListSerializer(entry)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_entry(self, request, pk=None):
        """
        Cancel a waiting list entry.
        Users can cancel their own entries, admins can cancel any entry.
        """
        entry = self.get_object()
        
        # Check permissions
        if request.user.role != 'ADMIN' and entry.user != request.user:
            return Response(
                {'detail': 'You can only cancel your own waiting list entries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use the service layer to cancel with proper position reordering
        cancelled_entry = WaitingListService.cancel_waiting_list_entry(
            entry_id=entry.id,
            user=request.user if request.user.role != 'ADMIN' else entry.user
        )
        
        # Return the cancelled entry
        output_serializer = WaitingListSerializer(cancelled_entry)
        return Response(output_serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-entries')
    def my_entries(self, request):
        """
        Get current user's waiting list entries.
        """
        entries = WaitingList.objects.filter(user=request.user).select_related('equipment')
        
        # Apply filters if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            entries = entries.filter(status=status_filter)
        
        equipment_filter = request.query_params.get('equipment')
        if equipment_filter:
            entries = entries.filter(equipment_id=equipment_filter)
        
        # Order by position
        entries = entries.order_by('equipment', 'position', 'created_at')
        
        serializer = WaitingListSerializer(entries, many=True)
        return Response(serializer.data)
