"""
Service layer for WaitingList operations with FIFO ordering and concurrency protection.
"""
from django.db import transaction
from django.db.models import Max, Q
from rest_framework.exceptions import ValidationError
from .models import WaitingList, Equipment


class WaitingListService:
    """
    Service for handling waiting list operations with proper FIFO ordering.
    """
    
    @staticmethod
    @transaction.atomic
    def join_waiting_list(user, equipment, requested_start_time, requested_end_time):
        """
        Add a user to the waiting list with proper FIFO position assignment.
        
        Uses select_for_update() to ensure concurrent position assignment is safe.
        
        Args:
            user: User instance
            equipment: Equipment instance
            requested_start_time: Requested booking start datetime
            requested_end_time: Requested booking end datetime
        
        Returns:
            WaitingList instance
        
        Raises:
            ValidationError: If duplicate entry or validation fails
        """
        # Lock the equipment to prevent concurrent position conflicts
        equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        
        # Check for duplicate active waiting list entry
        existing_entry = WaitingList.objects.filter(
            user=user,
            equipment=equipment,
            requested_start_time=requested_start_time,
            requested_end_time=requested_end_time,
            status=WaitingList.Status.WAITING
        ).exists()
        
        if existing_entry:
            raise ValidationError({
                'detail': 'You already have an active waiting list entry for this equipment and time period.'
            })
        
        # Get the next position for this equipment (FIFO)
        # Lock all waiting list entries for this equipment to prevent race conditions
        max_position = WaitingList.objects.filter(
            equipment=equipment,
            status=WaitingList.Status.WAITING
        ).select_for_update().aggregate(Max('position'))['position__max']
        
        next_position = (max_position or 0) + 1
        
        # Create the waiting list entry
        entry = WaitingList.objects.create(
            user=user,
            equipment=equipment,
            requested_start_time=requested_start_time,
            requested_end_time=requested_end_time,
            position=next_position,
            status=WaitingList.Status.WAITING
        )
        
        return entry
    
    @staticmethod
    @transaction.atomic
    def cancel_waiting_list_entry(entry_id, user):
        """
        Cancel a waiting list entry and reorder positions.
        
        Args:
            entry_id: ID of the waiting list entry
            user: User requesting cancellation
        
        Returns:
            Cancelled WaitingList instance
        
        Raises:
            ValidationError: If entry not found or user not authorized
        """
        # Lock the entry and equipment
        entry = WaitingList.objects.select_related('equipment').select_for_update().get(pk=entry_id)
        
        # Verify user owns the entry
        if entry.user != user:
            raise ValidationError({
                'detail': 'You can only cancel your own waiting list entries.'
            })
        
        # Verify entry is cancellable
        if entry.status != WaitingList.Status.WAITING:
            raise ValidationError({
                'detail': f'Cannot cancel entry with status: {entry.get_status_display()}'
            })
        
        # Lock all waiting list entries for this equipment
        equipment = Equipment.objects.select_for_update().get(pk=entry.equipment.pk)
        
        # Get the position of the entry being cancelled
        cancelled_position = entry.position
        
        # Mark the entry as cancelled
        entry.status = WaitingList.Status.CANCELLED
        entry.save()
        
        # Reorder positions for entries after the cancelled one
        entries_to_reorder = WaitingList.objects.filter(
            equipment=equipment,
            status=WaitingList.Status.WAITING,
            position__gt=cancelled_position
        ).select_for_update().order_by('position')
        
        for waiting_entry in entries_to_reorder:
            waiting_entry.position -= 1
            waiting_entry.save(update_fields=['position'])
        
        return entry
    
    @staticmethod
    @transaction.atomic
    def process_booking_cancellation(equipment, cancelled_start_time, cancelled_end_time):
        """
        Process waiting list when a booking is cancelled.
        
        Finds eligible waiting list entries and notifies the first one (FIFO).
        Does NOT automatically create a booking.
        
        Args:
            equipment: Equipment instance
            cancelled_start_time: Start time of cancelled booking
            cancelled_end_time: End time of cancelled booking
        
        Returns:
            WaitingList entry that was notified, or None if no eligible entries
        """
        # Lock the equipment
        equipment = Equipment.objects.select_for_update().get(pk=equipment.pk)
        
        # Find eligible waiting list entries
        # Entry is eligible if it overlaps with the cancelled booking time
        eligible_entries = WaitingList.objects.filter(
            equipment=equipment,
            status=WaitingList.Status.WAITING,
            requested_start_time__lt=cancelled_end_time,
            requested_end_time__gt=cancelled_start_time
        ).select_for_update().order_by('position', 'created_at')
        
        if not eligible_entries.exists():
            return None
        
        # Get the first eligible entry (FIFO)
        first_entry = eligible_entries.first()
        
        # Mark as notified
        first_entry.status = WaitingList.Status.NOTIFIED
        first_entry.save()
        
        return first_entry
    
    @staticmethod
    def get_user_position(entry_id):
        """
        Get the current position of a waiting list entry.
        
        Args:
            entry_id: ID of the waiting list entry
        
        Returns:
            Current position number
        """
        entry = WaitingList.objects.get(pk=entry_id)
        
        if entry.status != WaitingList.Status.WAITING:
            return None
        
        # Count how many entries are ahead of this one
        ahead_count = WaitingList.objects.filter(
            equipment=entry.equipment,
            status=WaitingList.Status.WAITING,
            position__lt=entry.position
        ).count()
        
        return ahead_count + 1
