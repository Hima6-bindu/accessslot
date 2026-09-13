"""
API views for user authentication and profile management.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    
    POST /api/auth/register/
    
    Body:
    {
        "username": "string",
        "email": "string",
        "password": "string",
        "password_confirm": "string",
        "first_name": "string" (optional),
        "last_name": "string" (optional),
        "role": "STUDENT|FACULTY|ADMIN" (optional, defaults to STUDENT)
    }
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            {
                'message': 'User registered successfully',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token generation endpoint that includes user data.
    
    POST /api/auth/login/
    
    Body:
    {
        "username": "string",
        "password": "string"
    }
    
    Response includes access token, refresh token, and user data.
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """
    Get current authenticated user's profile.
    
    GET /api/auth/profile/
    
    Returns full user profile information.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Update current user's profile.
    
    PUT/PATCH /api/auth/profile/update/
    
    Body:
    {
        "first_name": "string" (optional),
        "last_name": "string" (optional)
    }
    """
    serializer = UserUpdateSerializer(
        request.user,
        data=request.data,
        partial=request.method == 'PATCH'
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response(
        {
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user).data
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Change current user's password.
    
    POST /api/auth/password/change/
    
    Body:
    {
        "old_password": "string",
        "new_password": "string",
        "new_password_confirm": "string"
    }
    """
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response(
        {'message': 'Password changed successfully'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint (client should discard tokens).
    
    POST /api/auth/logout/
    
    Note: With JWT, logout is primarily handled client-side by discarding tokens.
    This endpoint exists for consistency and can be extended with token blacklisting.
    """
    return Response(
        {'message': 'Logged out successfully'},
        status=status.HTTP_200_OK
    )
