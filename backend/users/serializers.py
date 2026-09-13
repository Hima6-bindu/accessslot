"""
Serializers for user authentication and profile management.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_email(self, value):
        """
        Check that email is unique (case-insensitive).
        """
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate_username(self, value):
        """
        Check that username is unique (case-insensitive).
        """
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate(self, attrs):
        """
        Check that passwords match.
        """
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user with hashed password.
        """
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user information.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        
        return token
    
    def validate(self, attrs):
        """
        Override to include user data in response.
        """
        data = super().validate(attrs)
        
        # Add user information to response
        data['user'] = UserSerializer(self.user).data
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read operations).
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
            'created_at',
            'date_joined'
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'role',
            'is_active',
            'created_at',
            'date_joined'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile (excluding sensitive fields).
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
        ]
    
    def validate(self, attrs):
        """
        Ensure user can only update their own profile.
        """
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """
        Check that old password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """
        Check that new passwords match.
        """
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                "new_password_confirm": "New password fields didn't match."
            })
        return attrs
    
    def save(self):
        """
        Update user password.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
