"""
Pytest fixtures for equipment tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from equipment.models import Equipment

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for REST framework API client."""
    return APIClient()


@pytest.fixture
def student_user(db):
    """Fixture to create a student user."""
    return User.objects.create_user(
        username='student_equip',
        email='student_equip@test.com',
        password='testpass123',
        role=User.Role.STUDENT
    )


@pytest.fixture
def faculty_user(db):
    """Fixture to create a faculty user."""
    return User.objects.create_user(
        username='faculty_equip',
        email='faculty_equip@test.com',
        password='testpass123',
        role=User.Role.FACULTY
    )


@pytest.fixture
def admin_user(db):
    """Fixture to create an admin user."""
    return User.objects.create_user(
        username='admin_equip',
        email='admin_equip@test.com',
        password='testpass123',
        role=User.Role.ADMIN
    )


@pytest.fixture
def authenticated_student_client(api_client, student_user):
    """Fixture for authenticated API client with student user."""
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture
def authenticated_faculty_client(api_client, faculty_user):
    """Fixture for authenticated API client with faculty user."""
    api_client.force_authenticate(user=faculty_user)
    return api_client


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Fixture for authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_equipment(db):
    """Fixture to create sample equipment."""
    return Equipment.objects.create(
        name='3D Printer Alpha',
        description='High-resolution 3D printer',
        equipment_type='3D Printer',
        location='Room 101',
        status=Equipment.Status.AVAILABLE,
        max_booking_duration=4
    )


@pytest.fixture
def maintenance_equipment(db):
    """Fixture to create equipment under maintenance."""
    return Equipment.objects.create(
        name='Microscope Beta',
        description='Digital microscope',
        equipment_type='Microscope',
        location='Lab 202',
        status=Equipment.Status.MAINTENANCE,
        max_booking_duration=2
    )


@pytest.fixture
def disabled_equipment(db):
    """Fixture to create disabled equipment."""
    return Equipment.objects.create(
        name='Laser Cutter Gamma',
        description='Precision laser cutter',
        equipment_type='Laser Cutter',
        location='Workshop 303',
        status=Equipment.Status.DISABLED,
        max_booking_duration=3
    )


@pytest.fixture
def equipment(db):
    """Fixture to create equipment (alias for sample_equipment for Phase 4 tests)."""
    return Equipment.objects.create(
        name='Test Equipment',
        description='Equipment for testing',
        equipment_type='Test Type',
        location='Test Location',
        status=Equipment.Status.AVAILABLE,
        max_booking_duration=4
    )


# Booking-related fixtures

@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Fixture for authenticated API client with admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def admin_user(db):
    """Fixture to create an admin user."""
    return User.objects.create_user(
        username='admin_booking',
        email='admin_booking@test.com',
        password='testpass123',
        role=User.Role.ADMIN
    )
