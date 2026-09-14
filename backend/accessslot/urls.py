"""
URL configuration for accessslot project.
"""
from django.contrib import admin
from django.urls import path, include
from .health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('users.urls')),
    path('api/', include('equipment.urls')),
]
