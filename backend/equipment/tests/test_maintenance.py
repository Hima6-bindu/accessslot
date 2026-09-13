"""
Tests for Maintenance functionality.
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from equipment.models import Maintenance, Equipment, Booking
from users.models import User


@pytest.mark.django_db
class TestMaintenanceModel:
    """Test suite for Maintenance model."""
    
    def test_create_maintenance_with_valid_data(self, equipment, admin_user):
        """Test creating maintenance with valid data."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Scheduled maintenance',
            created_by=admin_user
        )
        
        assert maintenance.equipment == equipment
        assert maintenance.start_time == start_time
        assert maintenance.end_time == end_time
        assert maintenance.reason == 'Scheduled maintenance'
        assert maintenance.created_by == admin_user
    
    def test_maintenance_string_representation(self, equipment, admin_user):
        """Test __str__ method of Maintenance model."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        expected = f"{equipment.name} - Maintenance ({start_time.strftime('%Y-%m-%d %H:%M')})"
        assert str(maintenance) == expected
    
    def test_maintenance_end_before_start_validation(self, equipment, admin_user):
        """Test that end time must be after start time."""
        from django.core.exceptions import ValidationError
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time - timedelta(hours=1)  # End before start
        
        maintenance = Maintenance(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        with pytest.raises(ValidationError) as exc_info:
            maintenance.full_clean()
        
        assert 'end_time' in exc_info.value.message_dict
    
    def test_maintenance_is_active_property(self, equipment, admin_user):
        """Test is_active property."""
        # Create maintenance that is currently active
        start_time = timezone.now() - timedelta(hours=1)
        end_time = timezone.now() + timedelta(hours=1)
        
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        assert maintenance.is_active is True
    
    def test_maintenance_is_future_property(self, equipment, admin_user):
        """Test is_future property."""
        # Create future maintenance
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        assert maintenance.is_future is True


@pytest.mark.django_db
class TestMaintenanceAPI:
    """Test suite for Maintenance API endpoints."""
    
    def test_list_maintenance_as_authenticated_user(self, student_user, equipment, admin_user):
        """Test that authenticated users can list maintenance schedules."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create maintenance
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test maintenance',
            created_by=admin_user
        )
        
        response = client.get('/api/maintenance/')
        
        assert response.status_code == status.HTTP_200_OK
        # API uses pagination, so check results key
        assert len(response.data['results']) == 1
    
    def test_list_maintenance_unauthenticated(self):
        """Test that unauthenticated users cannot list maintenance."""
        client = APIClient()
        response = client.get('/api/maintenance/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_maintenance_as_admin(self, admin_user, equipment):
        """Test that admin can create maintenance."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        data = {
            'equipment': equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'reason': 'Scheduled maintenance'
        }
        
        response = client.post('/api/maintenance/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Maintenance.objects.count() == 1
        
        maintenance = Maintenance.objects.first()
        assert maintenance.equipment == equipment
        assert maintenance.created_by == admin_user
    
    def test_create_maintenance_as_student_fails(self, student_user, equipment):
        """Test that student cannot create maintenance."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        data = {
            'equipment': equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'reason': 'Test'
        }
        
        response = client.post('/api/maintenance/', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_maintenance_as_faculty_fails(self, faculty_user, equipment):
        """Test that faculty cannot create maintenance."""
        client = APIClient()
        client.force_authenticate(user=faculty_user)
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        data = {
            'equipment': equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'reason': 'Test'
        }
        
        response = client.post('/api/maintenance/', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_overlapping_maintenance_fails(self, admin_user, equipment):
        """Test that overlapping maintenance periods are rejected."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Create first maintenance
        start_time1 = timezone.now() + timedelta(days=1)
        end_time1 = start_time1 + timedelta(hours=4)
        Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time1,
            end_time=end_time1,
            reason='First maintenance',
            created_by=admin_user
        )
        
        # Try to create overlapping maintenance (2PM-6PM overlaps with 1PM-5PM)
        start_time2 = start_time1 + timedelta(hours=1)  # 1 hour after first starts
        end_time2 = end_time1 + timedelta(hours=1)  # 1 hour after first ends
        
        data = {
            'equipment': equipment.id,
            'start_time': start_time2.isoformat(),
            'end_time': end_time2.isoformat(),
            'reason': 'Second maintenance'
        }
        
        response = client.post('/api/maintenance/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'overlaps' in str(response.data).lower()
    
    def test_create_maintenance_with_existing_booking_fails(self, admin_user, student_user, equipment):
        """Test that maintenance cannot be created if it conflicts with confirmed bookings."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Create a confirmed booking
        booking_start = timezone.now() + timedelta(days=1, hours=2)
        booking_end = booking_start + timedelta(hours=2)
        Booking.objects.create(
            user=student_user,
            equipment=equipment,
            start_time=booking_start,
            end_time=booking_end,
            status=Booking.Status.CONFIRMED
        )
        
        # Try to create maintenance that overlaps with the booking
        maintenance_start = timezone.now() + timedelta(days=1)
        maintenance_end = maintenance_start + timedelta(hours=4)
        
        data = {
            'equipment': equipment.id,
            'start_time': maintenance_start.isoformat(),
            'end_time': maintenance_end.isoformat(),
            'reason': 'Maintenance'
        }
        
        response = client.post('/api/maintenance/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'conflicts' in str(response.data).lower() or 'booking' in str(response.data).lower()
    
    def test_update_maintenance_as_admin(self, admin_user, equipment):
        """Test that admin can update maintenance."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Create maintenance
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Original reason',
            created_by=admin_user
        )
        
        # Update the reason
        data = {
            'reason': 'Updated reason'
        }
        
        response = client.patch(f'/api/maintenance/{maintenance.id}/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        maintenance.refresh_from_db()
        assert maintenance.reason == 'Updated reason'
    
    def test_update_maintenance_as_student_fails(self, student_user, admin_user, equipment):
        """Test that student cannot update maintenance."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create maintenance
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        data = {'reason': 'Updated'}
        response = client.patch(f'/api/maintenance/{maintenance.id}/', data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_maintenance_as_admin(self, admin_user, equipment):
        """Test that admin can delete maintenance."""
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        # Create maintenance
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        response = client.delete(f'/api/maintenance/{maintenance.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Maintenance.objects.count() == 0
    
    def test_delete_maintenance_as_student_fails(self, student_user, admin_user, equipment):
        """Test that student cannot delete maintenance."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create maintenance
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        maintenance = Maintenance.objects.create(
            equipment=equipment,
            start_time=start_time,
            end_time=end_time,
            reason='Test',
            created_by=admin_user
        )
        
        response = client.delete(f'/api/maintenance/{maintenance.id}/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Maintenance.objects.count() == 1


@pytest.mark.django_db
class TestMaintenanceBookingIntegration:
    """Test suite for maintenance integration with bookings."""
    
    def test_booking_blocked_during_maintenance(self, student_user, equipment, admin_user):
        """Test that bookings are blocked during maintenance periods."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create maintenance
        maintenance_start = timezone.now() + timedelta(days=1)
        maintenance_end = maintenance_start + timedelta(hours=4)
        Maintenance.objects.create(
            equipment=equipment,
            start_time=maintenance_start,
            end_time=maintenance_end,
            reason='Maintenance',
            created_by=admin_user
        )
        
        # Try to create booking during maintenance
        booking_start = maintenance_start + timedelta(hours=1)
        booking_end = booking_start + timedelta(hours=1)
        
        data = {
            'equipment': equipment.id,
            'start_time': booking_start.isoformat(),
            'end_time': booking_end.isoformat()
        }
        
        response = client.post('/api/bookings/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'maintenance' in str(response.data).lower()
    
    def test_booking_allowed_before_maintenance(self, student_user, equipment, admin_user):
        """Test that bookings are allowed before maintenance periods."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create maintenance
        maintenance_start = timezone.now() + timedelta(days=1, hours=4)
        maintenance_end = maintenance_start + timedelta(hours=4)
        Maintenance.objects.create(
            equipment=equipment,
            start_time=maintenance_start,
            end_time=maintenance_end,
            reason='Maintenance',
            created_by=admin_user
        )
        
        # Create booking before maintenance
        booking_start = timezone.now() + timedelta(days=1)
        booking_end = booking_start + timedelta(hours=2)
        
        data = {
            'equipment': equipment.id,
            'start_time': booking_start.isoformat(),
            'end_time': booking_end.isoformat()
        }
        
        response = client.post('/api/bookings/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_booking_allowed_after_maintenance(self, student_user, equipment, admin_user):
        """Test that bookings are allowed after maintenance periods."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create maintenance
        maintenance_start = timezone.now() + timedelta(days=1)
        maintenance_end = maintenance_start + timedelta(hours=2)
        Maintenance.objects.create(
            equipment=equipment,
            start_time=maintenance_start,
            end_time=maintenance_end,
            reason='Maintenance',
            created_by=admin_user
        )
        
        # Create booking after maintenance
        booking_start = maintenance_end + timedelta(hours=1)
        booking_end = booking_start + timedelta(hours=2)
        
        data = {
            'equipment': equipment.id,
            'start_time': booking_start.isoformat(),
            'end_time': booking_end.isoformat()
        }
        
        response = client.post('/api/bookings/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
