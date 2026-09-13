"""
Tests for admin user management API.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role='ADMIN'
    )


@pytest.fixture
def second_admin_user(db):
    """Create a second admin user for testing."""
    return User.objects.create_user(
        username='admin2',
        email='admin2@test.com',
        password='testpass123',
        first_name='Second',
        last_name='Admin',
        role='ADMIN'
    )


@pytest.fixture
def student_user(db):
    """Create a student user for testing."""
    return User.objects.create_user(
        username='student_test',
        email='student@test.com',
        password='testpass123',
        first_name='Student',
        last_name='User',
        role='STUDENT'
    )


@pytest.fixture
def faculty_user(db):
    """Create a faculty user for testing."""
    return User.objects.create_user(
        username='faculty_test',
        email='faculty@test.com',
        password='testpass123',
        first_name='Faculty',
        last_name='User',
        role='FACULTY'
    )


@pytest.fixture
def admin_client(admin_user):
    """Create an authenticated admin client."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def student_client(student_user):
    """Create an authenticated student client."""
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def faculty_client(faculty_user):
    """Create an authenticated faculty client."""
    client = APIClient()
    client.force_authenticate(user=faculty_user)
    return client


@pytest.mark.django_db
class TestAdminUserList:
    """Test listing users as admin."""
    
    def test_admin_can_list_users(self, admin_client, student_user, faculty_user):
        """Admin can list all users."""
        response = admin_client.get('/api/auth/users/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3  # admin, student, faculty
    
    def test_student_cannot_list_users(self, student_client):
        """Student receives 403 when trying to list users."""
        response = student_client.get('/api/auth/users/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_faculty_cannot_list_users(self, faculty_client):
        """Faculty receives 403 when trying to list users."""
        response = faculty_client.get('/api/auth/users/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_unauthenticated_cannot_list_users(self):
        """Unauthenticated user receives 401."""
        client = APIClient()
        response = client.get('/api/auth/users/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_password_not_in_response(self, admin_client, student_user):
        """Password is never returned in user list."""
        response = admin_client.get('/api/auth/users/')
        
        assert response.status_code == status.HTTP_200_OK
        for user_data in response.data:
            assert 'password' not in user_data
            assert 'password_hash' not in user_data
    
    def test_search_by_username(self, admin_client, student_user, faculty_user):
        """Admin can search users by username."""
        response = admin_client.get('/api/auth/users/', {'search': 'student'})
        
        assert response.status_code == status.HTTP_200_OK
        # Handle pagination if enabled
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
        assert any(u['username'] == 'student_test' for u in data)
    
    def test_search_by_email(self, admin_client, student_user):
        """Admin can search users by email."""
        response = admin_client.get('/api/auth/users/', {'search': 'student@'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_filter_by_role(self, admin_client, student_user, faculty_user):
        """Admin can filter users by role."""
        response = admin_client.get('/api/auth/users/', {'role': 'STUDENT'})
        
        assert response.status_code == status.HTTP_200_OK
        # Handle pagination if enabled
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert all(u['role'] == 'STUDENT' for u in data)
    
    def test_filter_by_active_status(self, admin_client, student_user):
        """Admin can filter users by active status."""
        # Deactivate student
        student_user.is_active = False
        student_user.save()
        
        response = admin_client.get('/api/auth/users/', {'is_active': 'false'})
        
        assert response.status_code == status.HTTP_200_OK
        # Handle pagination if enabled
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert all(not u['is_active'] for u in data)


@pytest.mark.django_db
class TestAdminUserDetail:
    """Test viewing user details as admin."""
    
    def test_admin_can_view_user_details(self, admin_client, student_user):
        """Admin can view detailed user information."""
        response = admin_client.get(f'/api/auth/users/{student_user.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == student_user.username
        assert response.data['email'] == student_user.email
        assert 'password' not in response.data
    
    def test_student_cannot_view_user_details(self, student_client, admin_user):
        """Student receives 403 when trying to view user details."""
        response = student_client.get(f'/api/auth/users/{admin_user.id}/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_faculty_cannot_view_user_details(self, faculty_client, student_user):
        """Faculty receives 403 when trying to view user details."""
        response = faculty_client.get(f'/api/auth/users/{student_user.id}/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminUserUpdate:
    """Test updating users as admin."""
    
    def test_admin_can_update_user_name(self, admin_client, student_user):
        """Admin can update user's name."""
        response = admin_client.patch(
            f'/api/auth/users/{student_user.id}/',
            {'first_name': 'Updated', 'last_name': 'Name'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert student_user.first_name == 'Updated'
        assert student_user.last_name == 'Name'
    
    def test_admin_can_update_user_email(self, admin_client, student_user):
        """Admin can update user's email."""
        response = admin_client.patch(
            f'/api/auth/users/{student_user.id}/',
            {'email': 'newemail@test.com'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert student_user.email == 'newemail@test.com'
    
    def test_admin_can_update_user_role(self, admin_client, student_user):
        """Admin can update user's role."""
        response = admin_client.patch(
            f'/api/auth/users/{student_user.id}/',
            {'role': 'FACULTY'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert student_user.role == 'FACULTY'
    
    def test_admin_can_deactivate_user(self, admin_client, student_user):
        """Admin can deactivate a user."""
        response = admin_client.patch(
            f'/api/auth/users/{student_user.id}/',
            {'is_active': False},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert not student_user.is_active
    
    def test_cannot_deactivate_last_admin(self, admin_client, admin_user):
        """Cannot deactivate the last active admin."""
        response = admin_client.patch(
            f'/api/auth/users/{admin_user.id}/',
            {'is_active': False},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'last active admin' in str(response.data).lower()
    
    def test_can_deactivate_admin_if_another_exists(self, admin_client, admin_user, second_admin_user):
        """Can deactivate admin if another active admin exists."""
        response = admin_client.patch(
            f'/api/auth/users/{admin_user.id}/',
            {'is_active': False},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert not admin_user.is_active
    
    def test_cannot_remove_admin_role_from_last_admin(self, admin_client, admin_user):
        """Cannot remove admin role from the last active admin."""
        response = admin_client.patch(
            f'/api/auth/users/{admin_user.id}/',
            {'role': 'FACULTY'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'last active admin' in str(response.data).lower()
    
    def test_student_cannot_update_users(self, student_client, faculty_user):
        """Student receives 403 when trying to update users."""
        response = student_client.patch(
            f'/api/auth/users/{faculty_user.id}/',
            {'first_name': 'Hacked'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        faculty_user.refresh_from_db()
        assert faculty_user.first_name != 'Hacked'
    
    def test_faculty_cannot_update_users(self, faculty_client, student_user):
        """Faculty receives 403 when trying to update users."""
        response = faculty_client.patch(
            f'/api/auth/users/{student_user.id}/',
            {'first_name': 'Hacked'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        student_user.refresh_from_db()
        assert student_user.first_name != 'Hacked'
    
    def test_duplicate_email_rejected(self, admin_client, student_user, faculty_user):
        """Cannot update user with duplicate email."""
        response = admin_client.patch(
            f'/api/auth/users/{student_user.id}/',
            {'email': faculty_user.email},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSensitiveDataProtection:
    """Test that sensitive data is never exposed."""
    
    def test_password_never_in_list_response(self, admin_client, student_user):
        """Password is never returned in list."""
        response = admin_client.get('/api/auth/users/')
        
        assert response.status_code == status.HTTP_200_OK
        for user_data in response.data:
            assert 'password' not in user_data
    
    def test_password_never_in_detail_response(self, admin_client, student_user):
        """Password is never returned in detail view."""
        response = admin_client.get(f'/api/auth/users/{student_user.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'password' not in response.data
    
    def test_jwt_tokens_never_in_response(self, admin_client, student_user):
        """JWT tokens are never returned in user management API."""
        response = admin_client.get(f'/api/auth/users/{student_user.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'token' not in response.data
        assert 'access' not in response.data
        assert 'refresh' not in response.data


@pytest.mark.django_db
class TestUserDeletion:
    """Test that user deletion is not allowed."""
    
    def test_cannot_delete_user(self, admin_client, student_user):
        """DELETE method is not allowed for users."""
        response = admin_client.delete(f'/api/auth/users/{student_user.id}/')
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        # Verify user still exists
        assert User.objects.filter(id=student_user.id).exists()
