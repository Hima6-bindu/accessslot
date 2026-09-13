"""
API views for Booking management with concurrency protection.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db import transaction

from .models import Booking
from .booking_serializers import (
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingCancelSerializer,
    BookingListSerializer,
    BookingDetailSerializer
)
from .booking_services import BookingService
from users.permissions import IsAdmin, IsOwnerOrAdmin


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking CRUD operations with proper concurrency control.
    
    Permissions:
    - Create: Any authenticated user
    - List: Users see their own bookings, admins see all
    - Retrieve: Owner or admin
    - Update: Owner or admin
    - Cancel: Owner or admin
    
    POST   /api/bookings/                 - Create booking
    GET    /api/bookings/                 - List bookings (filtered by user)
    GET    /api/bookings/{id}/            - Retrieve booking details
    PATCH  /api/bookings/{id}/            - Update booking
    POST   /api/bookings/{id}/cancel/     - Cancel booking
    GET    /api/bookings/my-bookings/     - Current user's bookings
    """
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'equipment']
    ordering_fields = ['start_time', 'created_at']
    ordering = ['-start_time']
    
    def get_queryset(self):
        """
        Return bookings based on user role.
        Regular users see only their bookings, admins see all.
        """
        user = self.request.user
        
        if user.role == 'ADMIN':
            return Booking.objects.all().select_related('user', 'equipment')
        else:
            return Booking.objects.filter(user=user).select_related('equipment')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        elif self.action == 'cancel':
            return BookingCancelSerializer
        elif self.action == 'list' or self.action == 'my_bookings':
            return BookingListSerializer
        elif self.action == 'retrieve':
            return BookingDetailSerializer
        return BookingListSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'cancel']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking with conflict detection and usage limit validation.
        
        Uses the BookingService to handle concurrency with database locking.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated data
        equipment_id = serializer.validated_data['equipment'].id
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        
        try:
            # Use service layer for transaction and locking
            booking = BookingService.create_booking(
                user=request.user,
                equipment_id=equipment_id,
                start_time=start_time,
                end_time=end_time
            )
            
            # Serialize the created booking
            detail_serializer = BookingDetailSerializer(booking)
            
            return Response(
                {
                    'message': 'Booking created successfully',
                    'booking': detail_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            # Re-raise validation errors from service layer
            raise
    
    def list(self, request, *args, **kwargs):
        """
        List bookings with pagination.
        Users see their own bookings, admins see all.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve booking details.
        Only owner or admin can view.
        """
        instance = self.get_object()
        
        # Check permission (owner or admin)
        if instance.user != request.user and request.user.role != 'ADMIN':
            return Response(
                {'detail': 'You do not have permission to view this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Update booking (PATCH only, no PUT).
        
        Re-validates all booking rules including conflicts and usage limits.
        """
        partial = True  # Only allow partial updates
        instance = self.get_object()
        
        # Check permission (owner or admin)
        if instance.user != request.user and request.user.role != 'ADMIN':
            return Response(
                {'detail': 'You do not have permission to update this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated data
        start_time = serializer.validated_data.get('start_time')
        end_time = serializer.validated_data.get('end_time')
        
        try:
            # Use service layer for transaction and locking
            updated_booking = BookingService.update_booking(
                booking_id=instance.id,
                start_time=start_time,
                end_time=end_time
            )
            
            # Serialize the updated booking
            detail_serializer = BookingDetailSerializer(updated_booking)
            
            return Response(
                {
                    'message': 'Booking updated successfully',
                    'booking': detail_serializer.data
                }
            )
        
        except Exception as e:
            # Re-raise validation errors from service layer
            raise
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete is not allowed. Use cancel instead.
        """
        return Response(
            {'detail': 'Direct deletion is not allowed. Use the cancel endpoint instead.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        
        POST /api/bookings/{id}/cancel/
        Body: { "cancellation_reason": "optional reason" }
        """
        instance = self.get_object()
        
        # Check permission (owner or admin)
        if instance.user != request.user and request.user.role != 'ADMIN':
            return Response(
                {'detail': 'You do not have permission to cancel this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cancellation_reason = serializer.validated_data.get('cancellation_reason')
        
        try:
            # Use service layer for transaction (now returns booking and notified entry)
            cancelled_booking, notified_entry = BookingService.cancel_booking(
                booking_id=instance.id,
                cancellation_reason=cancellation_reason
            )
            
            # Serialize the cancelled booking
            detail_serializer = BookingDetailSerializer(cancelled_booking)
            
            response_data = {
                'message': 'Booking cancelled successfully',
                'booking': detail_serializer.data
            }
            
            # Include waiting list notification if someone was notified
            if notified_entry:
                response_data['waiting_list_notification'] = {
                    'notified': True,
                    'user': notified_entry.user.username,
                    'position': notified_entry.position,
                    'message': f'User {notified_entry.user.username} has been notified from the waiting list.'
                }
            
            return Response(response_data)
        
        except Exception as e:
            # Re-raise validation errors from service layer
            raise
    
    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """
        Get current user's bookings.
        
        GET /api/bookings/my-bookings/
        """
        queryset = Booking.objects.filter(user=request.user).select_related('equipment')
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
