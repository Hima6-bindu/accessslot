"""
Serializers for Maintenance model.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Maintenance, Equipment


class MaintenanceSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and retrieving maintenance records.
    """
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Maintenance
        fields = [
            'id',
            'equipment',
            'equipment_name',
            'start_time',
            'end_time',
            'reason',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class MaintenanceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating maintenance records.
    """
    
    class Meta:
        model = Maintenance
        fields = [
            'equipment',
            'start_time',
            'end_time',
            'reason',
        ]
    
    def validate(self, data):
        """
        Validate maintenance creation data.
        """
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Validate time range
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        # Validate equipment exists and get it
        equipment = data.get('equipment')
        if not equipment:
            raise serializers.ValidationError({
                'equipment': 'Equipment is required.'
            })
        
        return data
    
    def create(self, validated_data):
        """
        Create maintenance record with created_by set to request user.
        Note: Overlap validation is handled in the service layer.
        """
        # created_by will be set in the view
        return Maintenance.objects.create(**validated_data)


class MaintenanceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating maintenance records.
    """
    
    class Meta:
        model = Maintenance
        fields = [
            'start_time',
            'end_time',
            'reason',
        ]
    
    def validate(self, data):
        """
        Validate maintenance update data.
        """
        instance = self.instance
        start_time = data.get('start_time', instance.start_time)
        end_time = data.get('end_time', instance.end_time)
        
        # Validate time range
        if end_time <= start_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        return data
