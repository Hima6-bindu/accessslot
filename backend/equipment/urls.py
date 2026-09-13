"""
URL routing for equipment, booking, maintenance, and waiting list endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipmentViewSet
from .booking_views import BookingViewSet
from .maintenance_views import MaintenanceViewSet
from .waitinglist_views import WaitingListViewSet

app_name = 'equipment'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'equipment', EquipmentViewSet, basename='equipment')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'waiting-list', WaitingListViewSet, basename='waiting-list')

urlpatterns = [
    path('', include(router.urls)),
]
