"""
Tests for role-based permissions.
"""
import pytest
from django.contrib.auth import get_user_model
from users.permissions import (
    IsAdmin,
    IsFaculty,
    IsFacultyOrAdmin,
    IsStudent,
    IsAdminOrReadOnly
)
from rest_framework.test import APIRequestFactory

User = get_user_model()


@pytest.mark.django_db
class TestRoleBasedPermissions:
    """Test suite for role-based permission classes."""
    
    @pytest.fixture
    def factory(self):
        """Fixture for API request factory."""
        return APIRequestFactory()
    
    def test_is_admin_permission(self, factory, student_user, admin_user):
        """Test IsAdmin permission class."""
        permission = IsAdmin()
        
        # Test with admin user
        request = factory.get('/')
        request.user = admin_user
        assert permission.has_permission(request, None) is True
        
        # Test with student user
        request = factory.get('/')
        request.user = student_user
        assert permission.has_permission(request, None) is False
        
        # Test with unauthenticated user - create anonymous user mock
        from django.contrib.auth.models import AnonymousUser
        request = factory.get('/')
        request.user = AnonymousUser()
        assert permission.has_permission(request, None) is False
    
    def test_is_faculty_permission(self, factory, student_user, faculty_user):
        """Test IsFaculty permission class."""
        permission = IsFaculty()
        
        # Test with faculty user
        request = factory.get('/')
        request.user = faculty_user
        assert permission.has_permission(request, None) is True
        
        # Test with student user
        request = factory.get('/')
        request.user = student_user
        assert permission.has_permission(request, None) is False
    
    def test_is_faculty_or_admin_permission(
        self, factory, student_user, faculty_user, admin_user
    ):
        """Test IsFacultyOrAdmin permission class."""
        permission = IsFacultyOrAdmin()
        
        # Test with faculty user
        request = factory.get('/')
        request.user = faculty_user
        assert permission.has_permission(request, None) is True
        
        # Test with admin user
        request = factory.get('/')
        request.user = admin_user
        assert permission.has_permission(request, None) is True
        
        # Test with student user
        request = factory.get('/')
        request.user = student_user
        assert permission.has_permission(request, None) is False
    
    def test_is_student_permission(self, factory, student_user, faculty_user):
        """Test IsStudent permission class."""
        permission = IsStudent()
        
        # Test with student user
        request = factory.get('/')
        request.user = student_user
        assert permission.has_permission(request, None) is True
        
        # Test with faculty user
        request = factory.get('/')
        request.user = faculty_user
        assert permission.has_permission(request, None) is False
    
    def test_is_admin_or_read_only_permission(
        self, factory, student_user, admin_user
    ):
        """Test IsAdminOrReadOnly permission class."""
        permission = IsAdminOrReadOnly()
        
        # Test GET request with student (should allow)
        request = factory.get('/')
        request.user = student_user
        assert permission.has_permission(request, None) is True
        
        # Test POST request with student (should deny)
        request = factory.post('/')
        request.user = student_user
        assert permission.has_permission(request, None) is False
        
        # Test POST request with admin (should allow)
        request = factory.post('/')
        request.user = admin_user
        assert permission.has_permission(request, None) is True
        
        # Test PUT request with admin (should allow)
        request = factory.put('/')
        request.user = admin_user
        assert permission.has_permission(request, None) is True
