"""
Tests for Booking API endpoints.
"""
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from equipment.models import Booking, Equipment, UsageLimit


@pytest.mark.django_db
class TestBookingCreationAPI:
    """Test suite for booking creation endpoint."""
    
    def test_create_booking_success(self, authenticated_student_client, sample_equipment):
        """Test successful booking creation."""
        url = reverse('equipment:booking-list')
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'booking' in response.data
        assert response.data['booking']['status'] == 'CONFIRMED'
        assert Booking.objects.filter(equipment=sample_equipment).exists()
    
    def test_create_booking_unauthenticated(self, api_client, sample_equipment):
        """Test booking creation fails for unauthenticated user."""
        url = reverse('equipment:booking-list')
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_booking_start_time_in_past(self, authenticated_student_client, sample_equipment):
        """Test booking creation fails when start time is in past."""
        url = reverse('equipment:booking-list')
        start_time = timezone.now() - timedelta(hours=1)
        end_time = timezone.now() + timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'start_time' in str(response.data)
    
    def test_create_booking_end_before_start(self, authenticated_student_client, sample_equipment):
        """Test booking creation fails when end time before start time."""
        url = reverse('equipment:booking-list')
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time - timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_booking_exceeds_equipment_max_duration(self, authenticated_student_client, sample_equipment):
        """Test booking creation fails when duration exceeds equipment maximum."""
        url = reverse('equipment:booking-list')
        start_time = timezone.now() + timedelta(hours=1)
        # sample_equipment max_booking_duration is 4 hours
        end_time = start_time + timedelta(hours=5)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'duration' in str(response.data)
    
    def test_create_booking_equipment_unavailable(self, authenticated_student_client, maintenance_equipment):
        """Test booking creation fails for unavailable equipment."""
        url = reverse('equipment:booking-list')
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': maintenance_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'equipment' in str(response.data)


@pytest.mark.django_db
class TestBookingConflictDetection:
    """Test suite for booking conflict detection."""
    
    def test_exact_overlap_rejected(self, authenticated_student_client, sample_equipment):
        """Test exact time overlap is rejected."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        # Create first booking
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try to create overlapping booking
        url = reverse('equipment:booking-list')
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'BOOKING_CONFLICT' in str(response.data)
    
    def test_partial_overlap_beginning_rejected(self, authenticated_student_client, sample_equipment):
        """Test partial overlap at beginning is rejected."""
        # Existing: 2PM - 4PM
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=2)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try: 1PM - 3PM (overlaps beginning)
        url = reverse('equipment:booking-list')
        new_start = start_time - timedelta(hours=1)
        new_end = end_time - timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'BOOKING_CONFLICT' in str(response.data)
    
    def test_partial_overlap_end_rejected(self, authenticated_student_client, sample_equipment):
        """Test partial overlap at end is rejected."""
        # Existing: 2PM - 4PM
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=2)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try: 3PM - 5PM (overlaps end)
        url = reverse('equipment:booking-list')
        new_start = start_time + timedelta(hours=1)
        new_end = end_time + timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'BOOKING_CONFLICT' in str(response.data)
    
    def test_existing_inside_requested_rejected(self, authenticated_student_client, sample_equipment):
        """Test existing booking inside requested period is rejected."""
        # Existing: 2PM - 3PM
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try: 1PM - 4PM (contains existing)
        url = reverse('equipment:booking-list')
        new_start = start_time - timedelta(hours=1)
        new_end = end_time + timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'BOOKING_CONFLICT' in str(response.data)
    
    def test_requested_inside_existing_rejected(self, authenticated_student_client, sample_equipment):
        """Test requested booking inside existing period is rejected."""
        # Existing: 1PM - 5PM
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=4)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try: 2PM - 3PM (inside existing)
        url = reverse('equipment:booking-list')
        new_start = start_time + timedelta(hours=1)
        new_end = new_start + timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'BOOKING_CONFLICT' in str(response.data)
    
    def test_back_to_back_bookings_allowed(self, authenticated_student_client, sample_equipment):
        """Test back-to-back bookings are allowed (no overlap)."""
        # Existing: 2PM - 4PM
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=2)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try: 4PM - 6PM (immediately after, no overlap)
        url = reverse('equipment:booking-list')
        data = {
            'equipment': sample_equipment.id,
            'start_time': end_time.isoformat(),
            'end_time': (end_time + timedelta(hours=2)).isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_before_existing_booking_allowed(self, authenticated_student_client, sample_equipment):
        """Test booking before existing booking is allowed."""
        # Existing: 4PM - 6PM
        start_time = timezone.now() + timedelta(hours=4)
        end_time = start_time + timedelta(hours=2)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        # Try: 1PM - 2PM (before existing)
        url = reverse('equipment:booking-list')
        new_start = timezone.now() + timedelta(hours=1)
        new_end = new_start + timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_cancelled_booking_does_not_block(self, authenticated_student_client, sample_equipment):
        """Test cancelled bookings do not cause conflicts."""
        # Existing cancelled booking: 2PM - 4PM
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=2)
        
        Booking.objects.create(
            user=authenticated_student_client.handler._force_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CANCELLED  # Cancelled status
        )
        
        # Try same time slot - should succeed
        url = reverse('equipment:booking-list')
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestWeeklyUsageLimits:
    """Test suite for weekly usage limits."""
    
    def test_booking_within_limit_succeeds(self, authenticated_student_client, sample_equipment):
        """Test booking within weekly limit succeeds."""
        # Student limit is 4 hours, booking 2 hours should succeed
        url = reverse('equipment:booking-list')
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_booking_exceeding_limit_fails(self, authenticated_student_client, sample_equipment, student_user):
        """Test booking exceeding weekly limit fails."""
        # Create existing bookings totaling 3.5 hours
        base_time = timezone.now() + timedelta(hours=1)
        
        Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=base_time,
            end_time=base_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=base_time + timedelta(hours=3),
            end_time=base_time + timedelta(hours=4, minutes=30),
            status=Booking.Status.CONFIRMED
        )
        
        # Try to book 1 more hour (total would be 4.5 hours, exceeds 4 hour limit)
        url = reverse('equipment:booking-list')
        start_time = base_time + timedelta(hours=6)
        end_time = start_time + timedelta(hours=1)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'USAGE_LIMIT_EXCEEDED' in str(response.data)
    
    def test_cancelled_bookings_dont_count_toward_limit(self, authenticated_student_client, sample_equipment, student_user):
        """Test cancelled bookings don't count toward usage limit."""
        base_time = timezone.now() + timedelta(hours=1)
        
        # Create cancelled booking (3 hours)
        Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=base_time,
            end_time=base_time + timedelta(hours=3),
            status=Booking.Status.CANCELLED
        )
        
        # Try to book 3.5 hours - should succeed because cancelled doesn't count
        url = reverse('equipment:booking-list')
        start_time = base_time + timedelta(hours=5)
        end_time = start_time + timedelta(hours=3, minutes=30)
        
        data = {
            'equipment': sample_equipment.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestBookingListAPI:
    """Test suite for booking list endpoint."""
    
    def test_list_own_bookings(self, authenticated_student_client, student_user, sample_equipment):
        """Test user can list their own bookings."""
        # Create booking for user
        start_time = timezone.now() + timedelta(hours=1)
        Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-list')
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
    
    def test_user_cannot_see_others_bookings(
        self, authenticated_student_client, student_user, faculty_user, sample_equipment
    ):
        """Test user cannot see other users' bookings."""
        # Create booking for another user
        start_time = timezone.now() + timedelta(hours=1)
        Booking.objects.create(
            user=faculty_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-list')
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
    
    def test_admin_can_see_all_bookings(
        self, authenticated_admin_client, student_user, faculty_user, sample_equipment
    ):
        """Test admin can see all bookings."""
        start_time = timezone.now() + timedelta(hours=1)
        
        Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        Booking.objects.create(
            user=faculty_user,
            equipment=sample_equipment,
            start_time=start_time + timedelta(hours=3),
            end_time=start_time + timedelta(hours=5),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-list')
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
    
    def test_my_bookings_endpoint(self, authenticated_student_client, student_user, sample_equipment):
        """Test my-bookings endpoint."""
        start_time = timezone.now() + timedelta(hours=1)
        Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-my-bookings')
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1


@pytest.mark.django_db
class TestBookingCancellation:
    """Test suite for booking cancellation."""
    
    def test_cancel_own_booking(self, authenticated_student_client, student_user, sample_equipment):
        """Test user can cancel their own booking."""
        start_time = timezone.now() + timedelta(hours=1)
        booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-cancel', kwargs={'pk': booking.id})
        data = {'cancellation_reason': 'Test cancellation'}
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CANCELLED
        assert booking.cancellation_reason == 'Test cancellation'
    
    def test_cannot_cancel_others_booking(
        self, authenticated_student_client, faculty_user, sample_equipment
    ):
        """Test user cannot cancel another user's booking."""
        start_time = timezone.now() + timedelta(hours=1)
        booking = Booking.objects.create(
            user=faculty_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-cancel', kwargs={'pk': booking.id})
        response = authenticated_student_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestBookingUpdate:
    """Test suite for booking updates."""
    
    def test_update_own_booking(self, authenticated_student_client, student_user, sample_equipment):
        """Test user can update their own booking."""
        start_time = timezone.now() + timedelta(hours=1)
        booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        url = reverse('equipment:booking-detail', kwargs={'pk': booking.id})
        new_start = start_time + timedelta(hours=1)
        new_end = new_start + timedelta(hours=2)
        
        data = {
            'start_time': new_start.isoformat(),
            'end_time': new_end.isoformat()
        }
        
        response = authenticated_student_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        booking.refresh_from_db()
        assert booking.start_time.replace(microsecond=0) == new_start.replace(microsecond=0)
    
    def test_update_revalidates_conflicts(
        self, authenticated_student_client, student_user, sample_equipment
    ):
        """Test update revalidates booking conflicts."""
        # Create first booking: 2PM - 4PM
        start_time = timezone.now() + timedelta(hours=2)
        booking1 = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2),
            status=Booking.Status.CONFIRMED
        )
        
        # Create second booking: 5PM - 7PM
        booking2 = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time + timedelta(hours=3),
            end_time=start_time + timedelta(hours=5),
            status=Booking.Status.CONFIRMED
        )
        
        # Try to update booking2 to overlap with booking1
        url = reverse('equipment:booking-detail', kwargs={'pk': booking2.id})
        data = {
            'start_time': (start_time + timedelta(hours=1)).isoformat(),
            'end_time': (start_time + timedelta(hours=3)).isoformat()
        }
        
        response = authenticated_student_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'BOOKING_CONFLICT' in str(response.data)
