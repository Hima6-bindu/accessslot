"""
Pytest fixtures for user tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """
    Fixture for REST framework API client.
    """
    return APIClient()


@pytest.fixture
def student_user(db):
    """
    Fixture to create a student user.
    """
    return User.objects.create_user(
        username='student1',
        email='student1@test.com',
        password='testpass123',
        role=User.Role.STUDENT,
        first_name='Test',
        last_name='Student'
    )


@pytest.fixture
def faculty_user(db):
    """
    Fixture to create a faculty user.
    """
    return User.objects.create_user(
        username='faculty1',
        email='faculty1@test.com',
        password='testpass123',
        role=User.Role.FACULTY,
        first_name='Test',
        last_name='Faculty'
    )


@pytest.fixture
def admin_user(db):
    """
    Fixture to create an admin user.
    """
    return User.objects.create_user(
        username='admin1',
        email='admin1@test.com',
        password='testpass123',
        role=User.Role.ADMIN,
        first_name='Test',
        last_name='Admin'
    )


@pytest.fixture
def authenticated_client(api_client, student_user):
    """
    Fixture for authenticated API client with student user.
    """
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """
    Fixture for authenticated API client with admin user.
    """
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def faculty_client(api_client, faculty_user):
    """
    Fixture for authenticated API client with faculty user.
    """
    api_client.force_authenticate(user=faculty_user)
    return api_client
