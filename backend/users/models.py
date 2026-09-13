"""
User model with role-based functionality.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser with role-based access.
    
    Roles:
    - STUDENT: Regular students who can book equipment
    - FACULTY: Faculty members with extended privileges
    - ADMIN: Administrators with full system access
    """
    
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty'
        ADMIN = 'ADMIN', 'Admin'
    
    email = models.EmailField(
        unique=True,
        help_text='Required. Must be a valid email address.'
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='User role determining access level'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when user account was created'
    )
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        """Check if user is a student."""
        return self.role == self.Role.STUDENT
    
    @property
    def is_faculty(self):
        """Check if user is faculty."""
        return self.role == self.Role.FACULTY
    
    @property
    def is_admin_role(self):
        """Check if user is an admin (role-based, not Django superuser)."""
        return self.role == self.Role.ADMIN
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure email is lowercase and 
        admin role users have staff status.
        """
        self.email = self.email.lower()
        
        # Admin role users should have staff and superuser status
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        
        super().save(*args, **kwargs)
