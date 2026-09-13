"""
URL routing for authentication endpoints.
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import (
    UserRegistrationView,
    CustomTokenObtainPairView,
    current_user_view,
    update_profile_view,
    change_password_view,
    logout_view,
)
from .admin_views import AdminUserViewSet

app_name = 'users'

# Create router for admin user management
router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile management endpoints
    path('profile/', current_user_view, name='profile'),
    path('profile/update/', update_profile_view, name='profile_update'),
    path('password/change/', change_password_view, name='password_change'),
    
    # Admin user management endpoints
    path('', include(router.urls)),
]
