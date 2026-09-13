"""
Serializers for WaitingList model.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import WaitingList, Equipment


class WaitingListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and retrieving waiting list entries.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    
    class Meta:
        model = WaitingList
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'equipment',
            'equipment_name',
            'requested_start_time',
            'requested_end_time',
            'position',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'position', 'status', 'created_at', 'updated_at']


class WaitingListJoinSerializer(serializers.ModelSerializer):
    """
    Serializer for joining the waiting list.
    """
    
    class Meta:
        model = WaitingList
        fields = [
            'equipment',
            'requested_start_time',
            'requested_end_time',
        ]
    
    def validate(self, data):
        """
        Validate waiting list join data.
        """
        start_time = data.get('requested_start_time')
        end_time = data.get('requested_end_time')
        
        # Validate time range
        if end_time <= start_time:
            raise serializers.ValidationError({
                'requested_end_time': 'End time must be after start time.'
            })
        
        # Validate start time is in the future
        if start_time < timezone.now():
            raise serializers.ValidationError({
                'requested_start_time': 'Start time cannot be in the past.'
            })
        
        # Validate equipment exists
        equipment = data.get('equipment')
        if not equipment:
            raise serializers.ValidationError({
                'equipment': 'Equipment is required.'
            })
        
        return data


class WaitingListCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling a waiting list entry.
    """
    pass  # No additional fields needed for cancellation
