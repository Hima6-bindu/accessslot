"""
Equipment and Booking models for managing shared lab/college equipment.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Equipment(models.Model):
    """
    Model representing equipment available for booking.
    
    Examples: 3D printers, microscopes, lab equipment, etc.
    """
    
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        DISABLED = 'DISABLED', 'Disabled'
    
    name = models.CharField(
        max_length=200,
        help_text='Name of the equipment'
    )
    description = models.TextField(
        blank=True,
        help_text='Detailed description of the equipment'
    )
    equipment_type = models.CharField(
        max_length=100,
        help_text='Type/category of equipment (e.g., 3D Printer, Microscope)'
    )
    location = models.CharField(
        max_length=200,
        help_text='Physical location of the equipment'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        help_text='Current operational status of the equipment'
    )
    max_booking_duration = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Maximum booking duration in hours'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when equipment was added'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when equipment was last updated'
    )
    
    class Meta:
        db_table = 'equipment'
        ordering = ['name']
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['equipment_type']),
            models.Index(fields=['location']),
            models.Index(fields=['status', 'equipment_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.equipment_type})"
    
    def clean(self):
        """
        Validate model fields.
        """
        errors = {}
        
        if not self.name or not self.name.strip():
            errors['name'] = 'Name cannot be empty.'
        
        if not self.equipment_type or not self.equipment_type.strip():
            errors['equipment_type'] = 'Equipment type cannot be empty.'
        
        if not self.location or not self.location.strip():
            errors['location'] = 'Location cannot be empty.'
        
        if self.max_booking_duration is not None and self.max_booking_duration <= 0:
            errors['max_booking_duration'] = 'Maximum booking duration must be greater than 0.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save to run full_clean validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        """Check if equipment is currently available for booking."""
        return self.status == self.Status.AVAILABLE
    
    @property
    def is_under_maintenance(self):
        """Check if equipment is under maintenance."""
        return self.status == self.Status.MAINTENANCE
    
    @property
    def is_disabled(self):
        """Check if equipment is disabled."""
        return self.status == self.Status.DISABLED



class UsageLimit(models.Model):
    """
    Configuration model for weekly booking usage limits by role.
    """
    
    role = models.CharField(
        max_length=10,
        unique=True,
        help_text='User role (STUDENT, FACULTY)'
    )
    max_weekly_hours = models.PositiveIntegerField(
        help_text='Maximum booking hours per week'
    )
    
    class Meta:
        db_table = 'usage_limits'
        verbose_name = 'Usage Limit'
        verbose_name_plural = 'Usage Limits'
    
    def __str__(self):
        return f"{self.role}: {self.max_weekly_hours} hours/week"


class Booking(models.Model):
    """
    Model representing equipment bookings.
    
    Handles booking conflicts, concurrency, and weekly usage limits.
    """
    
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'
        NO_SHOW = 'NO_SHOW', 'No Show'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text='User who made the booking'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text='Equipment being booked'
    )
    start_time = models.DateTimeField(
        help_text='Booking start time'
    )
    end_time = models.DateTimeField(
        help_text='Booking end time'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
        help_text='Current status of the booking'
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for cancellation (if applicable)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when booking was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when booking was last updated'
    )
    
    class Meta:
        db_table = 'bookings'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['equipment', 'status']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['equipment', 'start_time', 'end_time']),
            models.Index(fields=['status', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.equipment.name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
    
    def clean(self):
        """
        Validate booking fields.
        """
        errors = {}
        
        # Validate time range
        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                errors['end_time'] = 'End time must be after start time.'
            
            # Check if start time is in the past
            if self.start_time < timezone.now():
                errors['start_time'] = 'Start time cannot be in the past.'
            
            # Check duration
            duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
            
            if duration_hours <= 0:
                errors['duration'] = 'Booking duration must be greater than zero.'
            
            # Check against equipment max booking duration
            if self.equipment and duration_hours > self.equipment.max_booking_duration:
                errors['duration'] = (
                    f'Booking duration ({duration_hours:.1f} hours) exceeds equipment '
                    f'maximum ({self.equipment.max_booking_duration} hours).'
                )
        
        # Check if equipment is available
        if self.equipment and self.equipment.status != Equipment.Status.AVAILABLE:
            errors['equipment'] = f'Equipment is currently {self.equipment.get_status_display().lower()}.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        Note: Conflict detection and usage limits are handled in the service layer
        with proper transaction locking.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_hours(self):
        """Calculate booking duration in hours."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return 0
    
    @property
    def is_confirmed(self):
        """Check if booking is confirmed."""
        return self.status == self.Status.CONFIRMED
    
    @property
    def is_cancelled(self):
        """Check if booking is cancelled."""
        return self.status == self.Status.CANCELLED
    
    @property
    def is_active(self):
        """Check if booking is active (confirmed and in the future)."""
        return self.status == self.Status.CONFIRMED and self.start_time > timezone.now()
    
    @property
    def is_past(self):
        """Check if booking is in the past."""
        return self.end_time < timezone.now()


class Maintenance(models.Model):
    """
    Model representing equipment maintenance periods.
    
    Prevents bookings during maintenance windows.
    """
    
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        help_text='Equipment under maintenance'
    )
    start_time = models.DateTimeField(
        help_text='Maintenance start time'
    )
    end_time = models.DateTimeField(
        help_text='Maintenance end time'
    )
    reason = models.TextField(
        help_text='Reason for maintenance'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_maintenance',
        help_text='Admin who scheduled the maintenance'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when maintenance was scheduled'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when maintenance was last updated'
    )
    
    class Meta:
        db_table = 'maintenance'
        ordering = ['-start_time']
        verbose_name = 'Maintenance'
        verbose_name_plural = 'Maintenance Records'
        indexes = [
            models.Index(fields=['equipment', 'start_time', 'end_time']),
            models.Index(fields=['start_time', 'end_time']),
        ]
    
    def __str__(self):
        return f"{self.equipment.name} - Maintenance ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
    
    def clean(self):
        """
        Validate maintenance fields.
        """
        errors = {}
        
        # Validate time range
        if self.end_time and self.start_time:
            if self.end_time <= self.start_time:
                errors['end_time'] = 'End time must be after start time.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        Note: Overlap detection is handled in the service layer.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if maintenance is currently active."""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    @property
    def is_future(self):
        """Check if maintenance is scheduled for the future."""
        return self.start_time > timezone.now()


class WaitingList(models.Model):
    """
    Model representing waiting list entries for equipment bookings.
    
    Manages FIFO queue when equipment is unavailable.
    """
    
    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        NOTIFIED = 'NOTIFIED', 'Notified'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FULFILLED = 'FULFILLED', 'Fulfilled'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='waiting_list_entries',
        help_text='User on the waiting list'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='waiting_list_entries',
        help_text='Equipment being requested'
    )
    requested_start_time = models.DateTimeField(
        help_text='Requested booking start time'
    )
    requested_end_time = models.DateTimeField(
        help_text='Requested booking end time'
    )
    position = models.PositiveIntegerField(
        help_text='Position in the waiting list (FIFO)'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING,
        help_text='Current status of the waiting list entry'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when added to waiting list'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when entry was last updated'
    )
    
    class Meta:
        db_table = 'waiting_list'
        ordering = ['equipment', 'position', 'created_at']
        verbose_name = 'Waiting List Entry'
        verbose_name_plural = 'Waiting List'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['equipment', 'status', 'position']),
            models.Index(fields=['equipment', 'requested_start_time', 'requested_end_time']),
            models.Index(fields=['status', 'position']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'equipment', 'requested_start_time', 'requested_end_time', 'status'],
                condition=models.Q(status='WAITING'),
                name='unique_active_waiting_entry'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.equipment.name} (Position {self.position})"
    
    def clean(self):
        """
        Validate waiting list entry fields.
        """
        errors = {}
        
        # Validate time range
        if self.requested_end_time and self.requested_start_time:
            if self.requested_end_time <= self.requested_start_time:
                errors['requested_end_time'] = 'End time must be after start time.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        Note: Position assignment is handled in the service layer.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_waiting(self):
        """Check if entry is in waiting status."""
        return self.status == self.Status.WAITING
    
    @property
    def is_notified(self):
        """Check if user has been notified."""
        return self.status == self.Status.NOTIFIED
