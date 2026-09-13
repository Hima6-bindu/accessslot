"""
Serializers for Equipment model.
"""
from rest_framework import serializers
from .models import Equipment


class EquipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Equipment model with validation.
    """
    
    class Meta:
        model = Equipment
        fields = [
            'id',
            'name',
            'description',
            'equipment_type',
            'location',
            'status',
            'max_booking_duration',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """
        Validate that name is not empty or whitespace only.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value.strip()
    
    def validate_equipment_type(self, value):
        """
        Validate that equipment_type is not empty or whitespace only.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Equipment type cannot be empty.")
        return value.strip()
    
    def validate_location(self, value):
        """
        Validate that location is not empty or whitespace only.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Location cannot be empty.")
        return value.strip()
    
    def validate_max_booking_duration(self, value):
        """
        Validate that max_booking_duration is greater than 0.
        """
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Maximum booking duration must be greater than 0."
            )
        return value
    
    def validate_status(self, value):
        """
        Validate that status is a valid choice.
        """
        if value not in [choice[0] for choice in Equipment.Status.choices]:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join([choice[0] for choice in Equipment.Status.choices])}"
            )
        return value


class EquipmentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for equipment list view.
    """
    
    class Meta:
        model = Equipment
        fields = [
            'id',
            'name',
            'equipment_type',
            'location',
            'status',
            'max_booking_duration'
        ]
        read_only_fields = fields


class EquipmentDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for equipment detail view with additional computed fields.
    """
    is_available = serializers.BooleanField(read_only=True)
    is_under_maintenance = serializers.BooleanField(read_only=True)
    is_disabled = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Equipment
        fields = [
            'id',
            'name',
            'description',
            'equipment_type',
            'location',
            'status',
            'max_booking_duration',
            'is_available',
            'is_under_maintenance',
            'is_disabled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'is_available',
            'is_under_maintenance',
            'is_disabled',
            'created_at',
            'updated_at'
        ]
