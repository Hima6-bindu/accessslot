"""
Service layer for Maintenance operations with conflict detection.
"""
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from .models import Maintenance, Booking, Equipment


class MaintenanceService:
    """
    Service for handling maintenance operations with proper validation.
    """
    
    @staticmethod
    @transaction.atomic
    def create_maintenance(equipment, start_time, end_time, reason, created_by):
        """
        Create a maintenance record with proper validation.
        
        Validates:
        - No overlapping maintenance periods for the same equipment
        - No confirmed bookings during the maintenance period
        
        Args:
            equipment: Equipment instance
            start_time: Maintenance start datetime
            end_time: Maintenance end datetime
            reason: Reason for maintenance
            created_by: User creating the maintenance
        
        Returns:
            Maintenance instance
        
        Raises:
            ValidationError: If validation fails
        """
        # Lock the equipment row to prevent concurrent conflicts
        equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        
        # Check for overlapping maintenance periods
        overlapping_maintenance = Maintenance.objects.filter(
            equipment=equipment,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        
        if overlapping_maintenance:
            raise ValidationError({
                'detail': 'Maintenance period overlaps with an existing maintenance schedule.'
            })
        
        # Check for confirmed bookings during the maintenance period
        conflicting_bookings = Booking.objects.filter(
            equipment=equipment,
            status=Booking.Status.CONFIRMED,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).select_related('user')
        
        if conflicting_bookings.exists():
            # Get the first conflicting booking for error message
            first_conflict = conflicting_bookings.first()
            raise ValidationError({
                'detail': (
                    f'Maintenance period conflicts with existing booking(s). '
                    f'First conflict: {first_conflict.user.username} '
                    f'from {first_conflict.start_time.strftime("%Y-%m-%d %H:%M")} '
                    f'to {first_conflict.end_time.strftime("%Y-%m-%d %H:%M")}. '
                    f'Please cancel or reschedule conflicting bookings first.'
                )
            })
        
        # Create the maintenance record
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
            created_by=created_by
        )
        
        return maintenance
    
    @staticmethod
    @transaction.atomic
    def update_maintenance(maintenance_id, start_time=None, end_time=None, reason=None):
        """
        Update a maintenance record with proper validation.
        
        Args:
            maintenance_id: ID of the maintenance to update
            start_time: New start time (optional)
            end_time: New end time (optional)
            reason: New reason (optional)
        
        Returns:
            Updated Maintenance instance
        
        Raises:
            ValidationError: If validation fails
        """
        # Lock the maintenance and equipment records
        maintenance = Maintenance.objects.select_related('equipment').select_for_update().get(pk=maintenance_id)
        equipment = Equipment.objects.select_for_update().get(pk=maintenance.equipment.pk)
        
        # Use current values if not provided
        new_start_time = start_time if start_time is not None else maintenance.start_time
        new_end_time = end_time if end_time is not None else maintenance.end_time
        
        # Check for overlapping maintenance periods (excluding current maintenance)
        overlapping_maintenance = Maintenance.objects.filter(
            equipment=equipment,
            start_time__lt=new_end_time,
            end_time__gt=new_start_time
        ).exclude(pk=maintenance_id).exists()
        
        if overlapping_maintenance:
            raise ValidationError({
                'detail': 'Updated maintenance period overlaps with another maintenance schedule.'
            })
        
        # Check for confirmed bookings during the new maintenance period
        conflicting_bookings = Booking.objects.filter(
            equipment=equipment,
            status=Booking.Status.CONFIRMED,
            start_time__lt=new_end_time,
            end_time__gt=new_start_time
        ).select_related('user')
        
        if conflicting_bookings.exists():
            first_conflict = conflicting_bookings.first()
            raise ValidationError({
                'detail': (
                    f'Updated maintenance period conflicts with existing booking(s). '
                    f'First conflict: {first_conflict.user.username} '
                    f'from {first_conflict.start_time.strftime("%Y-%m-%d %H:%M")} '
                    f'to {first_conflict.end_time.strftime("%Y-%m-%d %H:%M")}.'
                )
            })
        
        # Update the maintenance record
        if start_time is not None:
            maintenance.start_time = start_time
        if end_time is not None:
            maintenance.end_time = end_time
        if reason is not None:
            maintenance.reason = reason
        
        maintenance.save()
        return maintenance
    
    @staticmethod
    def check_maintenance_conflict(equipment, start_time, end_time):
        """
        Check if a time period conflicts with any maintenance.
        
        Args:
            equipment: Equipment instance
            start_time: Period start datetime
            end_time: Period end datetime
        
        Returns:
            Maintenance instance if conflict exists, None otherwise
        """
        return Maintenance.objects.filter(
            equipment=equipment,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).first()
