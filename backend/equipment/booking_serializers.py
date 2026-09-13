"""
Serializers for Booking model with validation.
"""
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Booking, Equipment

User = get_user_model()


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating bookings.
    Handles initial validation before service layer processing.
    """
    
    class Meta:
        model = Booking
        fields = [
            'equipment',
            'start_time',
            'end_time',
        ]
    
    def validate_start_time(self, value):
        """Validate that start time is not in the past."""
        if value < timezone.now():
            raise serializers.ValidationError("Start time cannot be in the past.")
        return value
    
    def validate(self, attrs):
        """Validate booking data."""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        equipment = attrs.get('equipment')
        
        # Validate time range
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        # Calculate duration
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        if duration_hours <= 0:
            raise serializers.ValidationError({
                'duration': 'Booking duration must be greater than zero.'
            })
        
        # Validate against equipment max booking duration
        if equipment and duration_hours > equipment.max_booking_duration:
            raise serializers.ValidationError({
                'duration': (
                    f'Booking duration ({duration_hours:.1f} hours) exceeds equipment '
                    f'maximum ({equipment.max_booking_duration} hours).'
                )
            })
        
        # Check if equipment is available
        if equipment and equipment.status != Equipment.Status.AVAILABLE:
            raise serializers.ValidationError({
                'equipment': f'Equipment is currently {equipment.get_status_display().lower()}.'
            })
        
        return attrs


class BookingUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating bookings.
    Only allows updating time fields for confirmed bookings.
    """
    
    class Meta:
        model = Booking
        fields = [
            'start_time',
            'end_time',
        ]
    
    def validate_start_time(self, value):
        """Validate that start time is not in the past."""
        if value < timezone.now():
            raise serializers.ValidationError("Start time cannot be in the past.")
        return value
    
    def validate(self, attrs):
        """Validate booking update."""
        instance = self.instance
        
        # Don't allow updates to cancelled bookings
        if instance.status == Booking.Status.CANCELLED:
            raise serializers.ValidationError("Cannot update cancelled bookings.")
        
        # Get start and end time (use existing if not provided)
        start_time = attrs.get('start_time', instance.start_time)
        end_time = attrs.get('end_time', instance.end_time)
        
        # Validate time range
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        # Calculate duration
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        if duration_hours <= 0:
            raise serializers.ValidationError({
                'duration': 'Booking duration must be greater than zero.'
            })
        
        # Validate against equipment max booking duration
        if duration_hours > instance.equipment.max_booking_duration:
            raise serializers.ValidationError({
                'duration': (
                    f'Booking duration ({duration_hours:.1f} hours) exceeds equipment '
                    f'maximum ({instance.equipment.max_booking_duration} hours).'
                )
            })
        
        return attrs


class BookingCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling bookings.
    """
    cancellation_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )


class BookingListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for booking list view.
    """
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_type = serializers.CharField(source='equipment.equipment_type', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id',
            'user_username',
            'equipment_name',
            'equipment_type',
            'start_time',
            'end_time',
            'status',
            'duration_hours',
            'created_at'
        ]
        read_only_fields = fields


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for booking detail view.
    """
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_type = serializers.CharField(source='equipment.equipment_type', read_only=True)
    equipment_location = serializers.CharField(source='equipment.location', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id',
            'user_username',
            'user_email',
            'equipment',
            'equipment_name',
            'equipment_type',
            'equipment_location',
            'start_time',
            'end_time',
            'status',
            'cancellation_reason',
            'duration_hours',
            'is_active',
            'is_past',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'user_username',
            'user_email',
            'equipment_name',
            'equipment_type',
            'equipment_location',
            'duration_hours',
            'is_active',
            'is_past',
            'created_at',
            'updated_at'
        ]
