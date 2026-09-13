"""
Tests for authentication endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test suite for user registration endpoint."""
    
    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        url = reverse('users:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['user']['role'] == 'STUDENT'
        assert 'password' not in response.data['user']
        
        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePass123!')
    
    def test_register_user_with_faculty_role(self, api_client):
        """Test user registration with faculty role."""
        url = reverse('users:register')
        data = {
            'username': 'facultyuser',
            'email': 'faculty@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'role': 'FACULTY'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['role'] == 'FACULTY'
    
    def test_register_user_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        url = reverse('users:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data
    
    def test_register_user_duplicate_email(self, api_client, student_user):
        """Test registration fails with duplicate email."""
        url = reverse('users:register')
        data = {
            'username': 'newuser',
            'email': student_user.email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_register_user_duplicate_username(self, api_client, student_user):
        """Test registration fails with duplicate username."""
        url = reverse('users:register')
        data = {
            'username': student_user.username,
            'email': 'different@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
    
    def test_register_user_weak_password(self, api_client):
        """Test registration fails with weak password."""
        url = reverse('users:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',
            'password_confirm': '123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_register_user_missing_required_fields(self, api_client):
        """Test registration fails with missing required fields."""
        url = reverse('users:register')
        data = {
            'username': 'newuser'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        assert 'password' in response.data


@pytest.mark.django_db
class TestUserLogin:
    """Test suite for user login endpoint."""
    
    def test_login_success(self, api_client, student_user):
        """Test successful login with valid credentials."""
        url = reverse('users:login')
        data = {
            'username': 'student1',
            'password': 'testpass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'student1'
        assert response.data['user']['role'] == 'STUDENT'
    
    def test_login_invalid_credentials(self, api_client, student_user):
        """Test login fails with invalid password."""
        url = reverse('users:login')
        data = {
            'username': 'student1',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, api_client):
        """Test login fails with nonexistent username."""
        url = reverse('users:login')
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, api_client, student_user):
        """Test login fails for inactive user."""
        student_user.is_active = False
        student_user.save()
        
        url = reverse('users:login')
        data = {
            'username': 'student1',
            'password': 'testpass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """Test suite for user profile endpoints."""
    
    def test_get_profile_authenticated(self, authenticated_client, student_user):
        """Test getting profile for authenticated user."""
        url = reverse('users:profile')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == student_user.username
        assert response.data['email'] == student_user.email
        assert response.data['role'] == student_user.role
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile fails for unauthenticated user."""
        url = reverse('users:profile')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_success(self, authenticated_client, student_user):
        """Test updating profile successfully."""
        url = reverse('users:profile_update')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['first_name'] == 'Updated'
        assert response.data['user']['last_name'] == 'Name'
        
        # Verify in database
        student_user.refresh_from_db()
        assert student_user.first_name == 'Updated'
        assert student_user.last_name == 'Name'
    
    def test_update_profile_partial(self, authenticated_client, student_user):
        """Test partial profile update with PATCH."""
        url = reverse('users:profile_update')
        data = {
            'first_name': 'OnlyFirst'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['first_name'] == 'OnlyFirst'
        # Last name should remain unchanged
        assert response.data['user']['last_name'] == student_user.last_name


@pytest.mark.django_db
class TestPasswordChange:
    """Test suite for password change endpoint."""
    
    def test_change_password_success(self, authenticated_client, student_user):
        """Test successful password change."""
        url = reverse('users:password_change')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        student_user.refresh_from_db()
        assert student_user.check_password('NewSecurePass123!')
    
    def test_change_password_wrong_old_password(self, authenticated_client):
        """Test password change fails with incorrect old password."""
        url = reverse('users:password_change')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'NewSecurePass123!'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
    
    def test_change_password_mismatch(self, authenticated_client):
        """Test password change fails when new passwords don't match."""
        url = reverse('users:password_change')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewSecurePass123!',
            'new_password_confirm': 'DifferentPass123!'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password_confirm' in response.data
    
    def test_change_password_weak_password(self, authenticated_client):
        """Test password change fails with weak new password."""
        url = reverse('users:password_change')
        data = {
            'old_password': 'testpass123',
            'new_password': '123',
            'new_password_confirm': '123'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data


@pytest.mark.django_db
class TestLogout:
    """Test suite for logout endpoint."""
    
    def test_logout_authenticated(self, authenticated_client):
        """Test logout for authenticated user."""
        url = reverse('users:logout')
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
    
    def test_logout_unauthenticated(self, api_client):
        """Test logout fails for unauthenticated user."""
        url = reverse('users:logout')
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
