"""
Tests for the public health check endpoint.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestHealthCheckEndpoint:
    """Test suite for the /api/health/ endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Health check should return HTTP 200."""
        url = reverse('health-check')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_requires_no_authentication(self, client):
        """Health check should work without authentication."""
        url = reverse('health-check')
        # No authentication headers
        response = client.get(url)
        
        # Should succeed without auth
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_returns_json(self, client):
        """Health check should return JSON response."""
        url = reverse('health-check')
        response = client.get(url)
        
        assert response['Content-Type'] == 'application/json'
    
    def test_health_check_status_ok(self, client):
        """Health check should return status: ok."""
        url = reverse('health-check')
        response = client.get(url)
        
        data = response.json()
        assert data['status'] == 'ok'
        assert 'service' in data
        assert data['service'] == 'AccessSlot API'
    
    def test_health_check_database_connected(self, client):
        """Health check should verify database connection."""
        url = reverse('health-check')
        response = client.get(url)
        
        data = response.json()
        assert 'database' in data
        assert data['database'] == 'connected'
    
    def test_health_check_get_only(self, client):
        """Health check should only accept GET requests."""
        url = reverse('health-check')
        
        # POST should not be allowed
        response = client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
