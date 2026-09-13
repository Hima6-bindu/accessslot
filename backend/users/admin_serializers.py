"""
Admin-specific serializers for user management.
These are separate from regular user serializers to maintain clear separation.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (admin only).
    Returns safe user information without sensitive data.
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'date_joined',
        ]
        read_only_fields = fields


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing detailed user information (admin only).
    """
    bookings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'date_joined',
            'created_at',
            'bookings_count',
        ]
        read_only_fields = fields
    
    def get_bookings_count(self, obj):
        """Get count of user's bookings."""
        return obj.bookings.count()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating users (admin only).
    Allows updating role and active status.
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'role',
            'is_active',
        ]
    
    def validate_email(self, value):
        """
        Check that email is unique (excluding current user).
        """
        user = self.instance
        if User.objects.filter(email__iexact=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, attrs):
        """
        Validate admin user update.
        Prevent deactivating the last active admin.
        """
        user = self.instance
        
        # Check if we're trying to deactivate an admin
        if 'is_active' in attrs and not attrs['is_active']:
            if user.role == 'ADMIN' and user.is_active:
                # Count active admins
                active_admins = User.objects.filter(
                    role='ADMIN',
                    is_active=True
                ).exclude(id=user.id).count()
                
                if active_admins == 0:
                    raise serializers.ValidationError({
                        'is_active': 'Cannot deactivate the last active admin account.'
                    })
        
        # Check if we're trying to change the role from admin
        if 'role' in attrs and user.role == 'ADMIN' and attrs['role'] != 'ADMIN':
            if user.is_active:
                # Count active admins
                active_admins = User.objects.filter(
                    role='ADMIN',
                    is_active=True
                ).exclude(id=user.id).count()
                
                if active_admins == 0:
                    raise serializers.ValidationError({
                        'role': 'Cannot remove admin role from the last active admin account.'
                    })
        
        return attrs
    
    def update(self, instance, validated_data):
        """
        Update user instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
