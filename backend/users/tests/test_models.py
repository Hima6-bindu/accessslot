"""
Tests for User model.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test suite for User model."""
    
    def test_create_user_with_default_role(self):
        """Test creating a user with default student role."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == User.Role.STUDENT
        assert user.is_active is True
        assert user.check_password('testpass123')
    
    def test_create_user_with_faculty_role(self):
        """Test creating a user with faculty role."""
        user = User.objects.create_user(
            username='faculty',
            email='faculty@example.com',
            password='testpass123',
            role=User.Role.FACULTY
        )
        assert user.role == User.Role.FACULTY
        assert user.is_faculty is True
        assert user.is_student is False
    
    def test_create_user_with_admin_role(self):
        """Test creating a user with admin role."""
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        assert user.role == User.Role.ADMIN
        assert user.is_admin_role is True
        assert user.is_staff is True
        assert user.is_superuser is True
    
    def test_email_is_lowercase(self):
        """Test that email is automatically converted to lowercase."""
        user = User.objects.create_user(
            username='testuser',
            email='TEST@EXAMPLE.COM',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
    
    def test_email_unique_constraint(self):
        """Test that email must be unique."""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123'
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='test@example.com',
                password='testpass123'
            )
    
    def test_username_unique_constraint(self):
        """Test that username must be unique."""
        User.objects.create_user(
            username='testuser',
            email='test1@example.com',
            password='testpass123'
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='testpass123'
            )
    
    def test_user_string_representation(self):
        """Test __str__ method of User model."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=User.Role.STUDENT
        )
        assert str(user) == 'testuser (Student)'
    
    def test_user_role_properties(self):
        """Test role helper properties."""
        student = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='testpass123',
            role=User.Role.STUDENT
        )
        assert student.is_student is True
        assert student.is_faculty is False
        assert student.is_admin_role is False
        
        faculty = User.objects.create_user(
            username='faculty',
            email='faculty@example.com',
            password='testpass123',
            role=User.Role.FACULTY
        )
        assert faculty.is_student is False
        assert faculty.is_faculty is True
        assert faculty.is_admin_role is False
        
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        assert admin.is_student is False
        assert admin.is_faculty is False
        assert admin.is_admin_role is True
