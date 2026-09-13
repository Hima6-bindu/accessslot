"""
Business logic services for booking management.
Handles conflict detection, concurrency control, and usage limits.
"""
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, datetime
from rest_framework.exceptions import ValidationError

from .models import Booking, Equipment, UsageLimit

User = get_user_model()


class MaintenanceConflictError(ValidationError):
    """Exception raised when a booking conflicts with maintenance."""
    def __init__(self, maintenance):
        super().__init__({
            'error': 'MAINTENANCE_CONFLICT',
            'message': (
                f'Equipment is scheduled for maintenance from '
                f'{maintenance.start_time.strftime("%Y-%m-%d %H:%M")} to '
                f'{maintenance.end_time.strftime("%Y-%m-%d %H:%M")}. '
                f'Reason: {maintenance.reason}'
            )
        })


class BookingConflictError(ValidationError):
    """Exception raised when a booking conflict is detected."""
    def __init__(self):
        super().__init__({
            'error': 'BOOKING_CONFLICT',
            'message': 'The equipment is already booked for the requested time.'
        })


class UsageLimitExceededError(ValidationError):
    """Exception raised when weekly usage limit is exceeded."""
    def __init__(self, used_hours, limit_hours, requested_hours):
        super().__init__({
            'error': 'USAGE_LIMIT_EXCEEDED',
            'message': (
                f'This booking would exceed your weekly usage limit. '
                f'Used: {used_hours:.1f}h, Limit: {limit_hours}h, Requested: {requested_hours:.1f}h'
            )
        })


class EquipmentUnavailableError(ValidationError):
    """Exception raised when equipment is unavailable."""
    def __init__(self, status):
        super().__init__({
            'error': 'EQUIPMENT_UNAVAILABLE',
            'message': f'This equipment is currently {status}.'
        })


class BookingService:
    """
    Service layer for booking operations with proper transaction handling.
    """
    
    @staticmethod
    def get_week_start_end(reference_date=None):
        """
        Get the start (Monday 00:00) and end (Sunday 23:59:59) of the week
        containing the reference date.
        """
        if reference_date is None:
            reference_date = timezone.now()
        
        # Get the Monday of the current week
        days_since_monday = reference_date.weekday()
        week_start = reference_date - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get the Sunday of the current week
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return week_start, week_end
    
    @staticmethod
    def calculate_weekly_usage(user, start_time, exclude_booking_id=None):
        """
        Calculate user's current weekly usage in hours.
        Only counts CONFIRMED bookings in the same week as start_time.
        """
        week_start, week_end = BookingService.get_week_start_end(start_time)
        
        # Get all confirmed bookings for the user in the current week
        bookings = Booking.objects.filter(
            user=user,
            status=Booking.Status.CONFIRMED,
            start_time__gte=week_start,
            start_time__lte=week_end
        )
        
        # Exclude current booking if updating
        if exclude_booking_id:
            bookings = bookings.exclude(id=exclude_booking_id)
        
        # Calculate total hours
        total_hours = 0
        for booking in bookings:
            duration = (booking.end_time - booking.start_time).total_seconds() / 3600
            total_hours += duration
        
        return total_hours
    
    @staticmethod
    def get_user_weekly_limit(user):
        """
        Get the weekly usage limit for a user based on their role.
        Returns the limit in hours, or None if no limit is set.
        """
        try:
            usage_limit = UsageLimit.objects.get(role=user.role)
            return usage_limit.max_weekly_hours
        except UsageLimit.DoesNotExist:
            # Default limits if not configured
            return 4 if user.role == 'STUDENT' else 8
    
    @staticmethod
    def check_booking_conflicts(equipment, start_time, end_time, exclude_booking_id=None):
        """
        Check for booking conflicts using the overlap detection rule.
        
        Overlap occurs when:
        existing.start_time < requested.end_time AND existing.end_time > requested.start_time
        
        This method should be called within a transaction with select_for_update().
        """
        conflicting_bookings = Booking.objects.filter(
            equipment=equipment,
            status=Booking.Status.CONFIRMED
        ).exclude(
            # Exclude the booking being updated
            id=exclude_booking_id
        ).filter(
            # Overlap detection: existing.start < new.end AND existing.end > new.start
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        return conflicting_bookings.exists()
    
    @staticmethod
    def check_usage_limit(user, start_time, end_time, exclude_booking_id=None):
        """
        Check if the booking would exceed the user's weekly usage limit.
        Raises UsageLimitExceededError if limit would be exceeded.
        """
        # Calculate current weekly usage
        current_usage = BookingService.calculate_weekly_usage(
            user, start_time, exclude_booking_id
        )
        
        # Calculate requested booking duration
        requested_duration = (end_time - start_time).total_seconds() / 3600
        
        # Get user's weekly limit
        weekly_limit = BookingService.get_user_weekly_limit(user)
        
        # Check if adding this booking would exceed the limit
        if current_usage + requested_duration > weekly_limit:
            raise UsageLimitExceededError(
                current_usage, weekly_limit, requested_duration
            )
    
    @staticmethod
    @transaction.atomic
    def create_booking(user, equipment_id, start_time, end_time):
        """
        Create a booking with proper conflict detection and concurrency control.
        
        Uses database-level locking to prevent race conditions.
        This method must be called within a transaction.
        """
        from .maintenance_services import MaintenanceService
        
        # Lock the equipment row to prevent concurrent bookings
        equipment = Equipment.objects.select_for_update().get(id=equipment_id)
        
        # Check if equipment is available
        if equipment.status != Equipment.Status.AVAILABLE:
            raise EquipmentUnavailableError(equipment.get_status_display().lower())
        
        # Check for maintenance conflicts
        maintenance_conflict = MaintenanceService.check_maintenance_conflict(
            equipment, start_time, end_time
        )
        if maintenance_conflict:
            raise MaintenanceConflictError(maintenance_conflict)
        
        # Check for booking conflicts with database lock
        if BookingService.check_booking_conflicts(equipment, start_time, end_time):
            raise BookingConflictError()
        
        # Check weekly usage limit
        BookingService.check_usage_limit(user, start_time, end_time)
        
        # Create the booking
        booking = Booking.objects.create(
            user=user,
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def update_booking(booking_id, start_time=None, end_time=None):
        """
        Update a booking with proper conflict detection.
        
        Re-validates all booking rules including conflicts and usage limits.
        """
        from .maintenance_services import MaintenanceService
        
        # Lock the booking and equipment
        booking = Booking.objects.select_for_update().select_related('equipment').get(id=booking_id)
        
        # Don't allow updates to cancelled bookings
        if booking.status == Booking.Status.CANCELLED:
            raise ValidationError({
                'error': 'INVALID_OPERATION',
                'message': 'Cannot update cancelled bookings.'
            })
        
        # Use existing values if not provided
        new_start_time = start_time if start_time is not None else booking.start_time
        new_end_time = end_time if end_time is not None else booking.end_time
        
        # Lock the equipment to prevent concurrent bookings
        equipment = Equipment.objects.select_for_update().get(id=booking.equipment.id)
        
        # Check if equipment is available
        if equipment.status != Equipment.Status.AVAILABLE:
            raise EquipmentUnavailableError(equipment.get_status_display().lower())
        
        # Check for maintenance conflicts
        maintenance_conflict = MaintenanceService.check_maintenance_conflict(
            equipment, new_start_time, new_end_time
        )
        if maintenance_conflict:
            raise MaintenanceConflictError(maintenance_conflict)
        
        # Check for conflicts (excluding this booking)
        if BookingService.check_booking_conflicts(
            equipment, new_start_time, new_end_time, exclude_booking_id=booking.id
        ):
            raise BookingConflictError()
        
        # Check weekly usage limit (excluding this booking)
        BookingService.check_usage_limit(
            booking.user, new_start_time, new_end_time, exclude_booking_id=booking.id
        )
        
        # Update the booking
        booking.start_time = new_start_time
        booking.end_time = new_end_time
        booking.save()
        
        return booking
    
    @staticmethod
    @transaction.atomic
    def cancel_booking(booking_id, cancellation_reason=None):
        """
        Cancel a booking and process the waiting list.
        """
        from .waitinglist_services import WaitingListService
        
        booking = Booking.objects.select_for_update().get(id=booking_id)
        
        # Don't allow cancelling already cancelled bookings
        if booking.status == Booking.Status.CANCELLED:
            raise ValidationError({
                'error': 'INVALID_OPERATION',
                'message': 'Booking is already cancelled.'
            })
        
        # Only allow cancelling confirmed bookings
        if booking.status != Booking.Status.CONFIRMED:
            raise ValidationError({
                'error': 'INVALID_OPERATION',
                'message': 'Only confirmed bookings can be cancelled.'
            })
        
        # Store booking details for waiting list processing
        equipment = booking.equipment
        start_time = booking.start_time
        end_time = booking.end_time
        
        # Update booking status
        booking.status = Booking.Status.CANCELLED
        if cancellation_reason:
            booking.cancellation_reason = cancellation_reason
        booking.save()
        
        # Process waiting list for this equipment/time
        notified_entry = WaitingListService.process_booking_cancellation(
            equipment, start_time, end_time
        )
        
        # Return both the booking and the notified waiting list entry (if any)
        return booking, notified_entry
