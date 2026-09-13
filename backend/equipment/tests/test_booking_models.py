"""
Tests for Booking model.
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from equipment.models import Booking, Equipment, UsageLimit
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestBookingModel:
    """Test suite for Booking model."""
    
    def test_create_booking_with_valid_data(self, student_user, sample_equipment):
        """Test creating booking with valid data."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        
        assert booking.user == student_user
        assert booking.equipment == sample_equipment
        assert booking.status == Booking.Status.CONFIRMED
        assert booking.duration_hours == 2.0
    
    def test_booking_default_status(self, student_user, sample_equipment):
        """Test booking default status is CONFIRMED."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time
        )
        
        assert booking.status == Booking.Status.CONFIRMED
    
    def test_booking_status_choices(self, student_user, sample_equipment):
        """Test all status choices are valid."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        statuses = [
            Booking.Status.CONFIRMED,
            Booking.Status.CANCELLED,
            Booking.Status.COMPLETED,
            Booking.Status.NO_SHOW
        ]
        
        for status in statuses:
            booking = Booking.objects.create(
                user=student_user,
                equipment=sample_equipment,
                start_time=start_time + timedelta(days=statuses.index(status)),
                end_time=end_time + timedelta(days=statuses.index(status)),
                status=status
            )
            assert booking.status == status
    
    def test_booking_string_representation(self, student_user, sample_equipment):
        """Test __str__ method of Booking model."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time
        )
        
        expected = f"{student_user.username} - {sample_equipment.name}"
        assert expected in str(booking)
    
    def test_booking_duration_hours_property(self, student_user, sample_equipment):
        """Test duration_hours property calculation."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=3, minutes=30)
        
        booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time
        )
        
        assert booking.duration_hours == 3.5
    
    def test_booking_status_properties(self, student_user, sample_equipment):
        """Test status helper properties."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        # Test CONFIRMED
        confirmed_booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED
        )
        assert confirmed_booking.is_confirmed is True
        assert confirmed_booking.is_cancelled is False
        
        # Test CANCELLED
        cancelled_booking = Booking.objects.create(
            user=student_user,
            equipment=sample_equipment,
            start_time=start_time + timedelta(days=1),
            end_time=end_time + timedelta(days=1),
            status=Booking.Status.CANCELLED
        )
        assert cancelled_booking.is_confirmed is False
        assert cancelled_booking.is_cancelled is True
    
    def test_booking_end_time_before_start_time(self, student_user, sample_equipment):
        """Test validation: end_time must be after start_time."""
        start_time = timezone.now() + timedelta(hours=2)
        end_time = start_time - timedelta(hours=1)  # Before start time
        
        with pytest.raises(ValidationError) as exc_info:
            Booking.objects.create(
                user=student_user,
                equipment=sample_equipment,
                start_time=start_time,
                end_time=end_time
            )
        
        assert 'end_time' in exc_info.value.message_dict
    
    def test_booking_start_time_in_past(self, student_user, sample_equipment):
        """Test validation: start_time cannot be in the past."""
        start_time = timezone.now() - timedelta(hours=1)
        end_time = timezone.now() + timedelta(hours=1)
        
        with pytest.raises(ValidationError) as exc_info:
            Booking.objects.create(
                user=student_user,
                equipment=sample_equipment,
                start_time=start_time,
                end_time=end_time
            )
        
        assert 'start_time' in exc_info.value.message_dict
    
    def test_booking_duration_exceeds_equipment_max(self, student_user, sample_equipment):
        """Test validation: duration cannot exceed equipment max."""
        start_time = timezone.now() + timedelta(hours=1)
        # sample_equipment has max_booking_duration of 4 hours
        end_time = start_time + timedelta(hours=5)  # Exceeds max
        
        with pytest.raises(ValidationError) as exc_info:
            Booking.objects.create(
                user=student_user,
                equipment=sample_equipment,
                start_time=start_time,
                end_time=end_time
            )
        
        assert 'duration' in exc_info.value.message_dict
    
    def test_booking_equipment_unavailable(self, student_user, maintenance_equipment):
        """Test validation: cannot book unavailable equipment."""
        start_time = timezone.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        with pytest.raises(ValidationError) as exc_info:
            Booking.objects.create(
                user=student_user,
                equipment=maintenance_equipment,
                start_time=start_time,
                end_time=end_time
            )
        
        assert 'equipment' in exc_info.value.message_dict


@pytest.mark.django_db
class TestUsageLimitModel:
    """Test suite for UsageLimit model."""
    
    def test_usage_limit_creation(self):
        """Test creating usage limit with custom role."""
        usage_limit = UsageLimit.objects.create(
            role='ADMIN',
            max_weekly_hours=12
        )
        
        assert usage_limit.role == 'ADMIN'
        assert usage_limit.max_weekly_hours == 12
    
    def test_usage_limit_unique_role(self):
        """Test role must be unique."""
        # STUDENT already exists from migration, try to create duplicate
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            UsageLimit.objects.create(role='STUDENT', max_weekly_hours=6)
    
    def test_usage_limit_string_representation(self):
        """Test __str__ method of UsageLimit model."""
        # FACULTY already exists from migration (8 hours/week)
        usage_limit = UsageLimit.objects.get(role='FACULTY')
        
        assert str(usage_limit) == 'FACULTY: 8 hours/week'
