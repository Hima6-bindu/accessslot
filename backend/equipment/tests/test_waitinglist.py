"""
Tests for WaitingList functionality.
"""
import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from equipment.models import WaitingList, Equipment, Booking
from users.models import User


@pytest.mark.django_db
class TestWaitingListModel:
    """Test suite for WaitingList model."""
    
    def test_create_waiting_list_entry_with_valid_data(self, student_user, equipment):
        """Test creating waiting list entry with valid data."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        entry = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        assert entry.user == student_user
        assert entry.equipment == equipment
        assert entry.position == 1
        assert entry.status == WaitingList.Status.WAITING
    
    def test_waiting_list_default_status(self, student_user, equipment):
        """Test that default status is WAITING."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        entry = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1
        )
        
        assert entry.status == WaitingList.Status.WAITING
    
    def test_waiting_list_string_representation(self, student_user, equipment):
        """Test __str__ method of WaitingList model."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        entry = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=3
        )
        
        expected = f"{student_user.username} - {equipment.name} (Position 3)"
        assert str(entry) == expected
    
    def test_waiting_list_end_before_start_validation(self, student_user, equipment):
        """Test that end time must be after start time."""
        from django.core.exceptions import ValidationError
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time - timedelta(hours=1)  # End before start
        
        entry = WaitingList(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1
        )
        
        with pytest.raises(ValidationError) as exc_info:
            entry.full_clean()
        
        assert 'requested_end_time' in exc_info.value.message_dict
    
    def test_waiting_list_is_waiting_property(self, student_user, equipment):
        """Test is_waiting property."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        entry = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        assert entry.is_waiting is True
    
    def test_waiting_list_is_notified_property(self, student_user, equipment):
        """Test is_notified property."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        entry = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1,
            status=WaitingList.Status.NOTIFIED
        )
        
        assert entry.is_notified is True


@pytest.mark.django_db
class TestWaitingListAPI:
    """Test suite for WaitingList API endpoints."""
    
    def test_join_waiting_list_success(self, student_user, equipment):
        """Test that user can join waiting list."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': equipment.id,
            'requested_start_time': start_time.isoformat(),
            'requested_end_time': end_time.isoformat()
        }
        
        response = client.post('/api/waiting-list/join/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert WaitingList.objects.count() == 1
        
        entry = WaitingList.objects.first()
        assert entry.user == student_user
        assert entry.equipment == equipment
        assert entry.position == 1
        assert entry.status == WaitingList.Status.WAITING
    
    def test_join_waiting_list_unauthenticated(self, equipment):
        """Test that unauthenticated users cannot join waiting list."""
        client = APIClient()
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': equipment.id,
            'requested_start_time': start_time.isoformat(),
            'requested_end_time': end_time.isoformat()
        }
        
        response = client.post('/api/waiting-list/join/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_join_waiting_list_duplicate_entry_fails(self, student_user, equipment):
        """Test that duplicate waiting list entries are rejected."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': equipment.id,
            'requested_start_time': start_time.isoformat(),
            'requested_end_time': end_time.isoformat()
        }
        
        # First join - should succeed
        response1 = client.post('/api/waiting-list/join/', data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second join with same details - should fail
        response2 = client.post('/api/waiting-list/join/', data, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already' in str(response2.data).lower()
    
    def test_join_waiting_list_fifo_ordering(self, student_user, faculty_user, equipment):
        """Test that waiting list maintains FIFO ordering."""
        client1 = APIClient()
        client1.force_authenticate(user=student_user)
        
        client2 = APIClient()
        client2.force_authenticate(user=faculty_user)
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': equipment.id,
            'requested_start_time': start_time.isoformat(),
            'requested_end_time': end_time.isoformat()
        }
        
        # First user joins
        response1 = client1.post('/api/waiting-list/join/', data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED
        assert response1.data['position'] == 1
        
        # Second user joins
        response2 = client2.post('/api/waiting-list/join/', data, format='json')
        assert response2.status_code == status.HTTP_201_CREATED
        assert response2.data['position'] == 2
    
    def test_list_own_waiting_list_entries(self, student_user, faculty_user, equipment):
        """Test that users can only see their own entries."""
        # Create entries for both users
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1
        )
        
        WaitingList.objects.create(
            user=faculty_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=2
        )
        
        # Student user should only see their own entry
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        response = client.get('/api/waiting-list/')
        
        assert response.status_code == status.HTTP_200_OK
        # API uses pagination, so check results key
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['user'] == student_user.id
    
    def test_admin_can_see_all_waiting_list_entries(self, admin_user, student_user, faculty_user, equipment):
        """Test that admin can see all entries."""
        # Create entries for both users
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1
        )
        
        WaitingList.objects.create(
            user=faculty_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=2
        )
        
        # Admin should see all entries
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.get('/api/waiting-list/')
        
        assert response.status_code == status.HTTP_200_OK
        # API uses pagination, so check results key
        assert len(response.data['results']) == 2
    
    def test_cancel_own_waiting_list_entry(self, student_user, equipment):
        """Test that user can cancel their own waiting list entry."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create waiting list entry
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        entry = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        # Cancel the entry
        response = client.post(f'/api/waiting-list/{entry.id}/cancel/')
        
        assert response.status_code == status.HTTP_200_OK
        
        entry.refresh_from_db()
        assert entry.status == WaitingList.Status.CANCELLED
    
    def test_cancel_others_waiting_list_entry_fails(self, student_user, faculty_user, equipment):
        """Test that user cannot cancel another user's entry."""
        # Create entry for faculty user
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        entry = WaitingList.objects.create(
            user=faculty_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        # Try to cancel as student user
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        response = client.post(f'/api/waiting-list/{entry.id}/cancel/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Not in their queryset
    
    def test_cancel_reorders_positions(self, student_user, faculty_user, equipment):
        """Test that cancelling entry reorders positions."""
        # Create multiple entries
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        entry1 = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        entry2 = WaitingList.objects.create(
            user=faculty_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=2,
            status=WaitingList.Status.WAITING
        )
        
        # Cancel first entry as admin
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        response = client.post(f'/api/waiting-list/{entry1.id}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        
        # Check that second entry moved to position 1
        entry2.refresh_from_db()
        assert entry2.position == 1
    
    def test_my_entries_endpoint(self, student_user, equipment):
        """Test my-entries endpoint."""
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        # Create multiple entries for the user
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=2)
        
        WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time,
            requested_end_time=end_time,
            position=1
        )
        
        WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=start_time + timedelta(days=1),
            requested_end_time=end_time + timedelta(days=1),
            position=2
        )
        
        response = client.get('/api/waiting-list/my-entries/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestWaitingListBookingIntegration:
    """Test suite for waiting list integration with bookings."""
    
    def test_booking_cancellation_notifies_waiting_list(self, student_user, faculty_user, equipment):
        """Test that cancelling a booking notifies first waiting list entry."""
        # Create a booking
        booking_start = timezone.now() + timedelta(days=1)
        booking_end = booking_start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=student_user,
            equipment=equipment,
            start_time=booking_start,
            end_time=booking_end,
            status=Booking.Status.CONFIRMED
        )
        
        # Create waiting list entry that overlaps
        WaitingList.objects.create(
            user=faculty_user,
            equipment=equipment,
            requested_start_time=booking_start,
            requested_end_time=booking_end,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        # Cancel the booking
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        response = client.post(f'/api/bookings/{booking.id}/cancel/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'waiting_list_notification' in response.data
        assert response.data['waiting_list_notification']['notified'] is True
        
        # Check that waiting list entry was notified
        entry = WaitingList.objects.first()
        assert entry.status == WaitingList.Status.NOTIFIED
    
    def test_booking_cancellation_no_waiting_list(self, student_user, equipment):
        """Test that cancelling booking works when no waiting list entries exist."""
        # Create a booking
        booking_start = timezone.now() + timedelta(days=1)
        booking_end = booking_start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=student_user,
            equipment=equipment,
            start_time=booking_start,
            end_time=booking_end,
            status=Booking.Status.CONFIRMED
        )
        
        # Cancel the booking
        client = APIClient()
        client.force_authenticate(user=student_user)
        
        response = client.post(f'/api/bookings/{booking.id}/cancel/')
        
        assert response.status_code == status.HTTP_200_OK
        # Should not have waiting list notification
        assert 'waiting_list_notification' not in response.data or \
               response.data.get('waiting_list_notification') is None
    
    def test_waiting_list_fifo_with_multiple_entries(self, student_user, faculty_user, equipment, admin_user):
        """Test that waiting list processes FIFO correctly with multiple entries."""
        # Create a booking
        booking_start = timezone.now() + timedelta(days=1)
        booking_end = booking_start + timedelta(hours=2)
        booking = Booking.objects.create(
            user=admin_user,
            equipment=equipment,
            start_time=booking_start,
            end_time=booking_end,
            status=Booking.Status.CONFIRMED
        )
        
        # Create multiple waiting list entries
        entry1 = WaitingList.objects.create(
            user=student_user,
            equipment=equipment,
            requested_start_time=booking_start,
            requested_end_time=booking_end,
            position=1,
            status=WaitingList.Status.WAITING
        )
        
        entry2 = WaitingList.objects.create(
            user=faculty_user,
            equipment=equipment,
            requested_start_time=booking_start,
            requested_end_time=booking_end,
            position=2,
            status=WaitingList.Status.WAITING
        )
        
        # Cancel the booking
        client = APIClient()
        client.force_authenticate(user=admin_user)
        
        response = client.post(f'/api/bookings/{booking.id}/cancel/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that first entry was notified, second is still waiting
        entry1.refresh_from_db()
        entry2.refresh_from_db()
        
        assert entry1.status == WaitingList.Status.NOTIFIED
        assert entry2.status == WaitingList.Status.WAITING
