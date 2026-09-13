"""
Tests for Equipment API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from equipment.models import Equipment


@pytest.mark.django_db
class TestEquipmentListAPI:
    """Test suite for equipment list endpoint."""
    
    def test_list_equipment_authenticated(self, authenticated_student_client, sample_equipment):
        """Test listing equipment with authenticated user."""
        url = reverse('equipment:equipment-list')
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == sample_equipment.name
    
    def test_list_equipment_unauthenticated(self, api_client, sample_equipment):
        """Test listing equipment fails for unauthenticated user."""
        url = reverse('equipment:equipment-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_multiple_equipment(
        self, authenticated_student_client, sample_equipment, maintenance_equipment, disabled_equipment
    ):
        """Test listing multiple equipment items."""
        url = reverse('equipment:equipment-list')
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3
    
    def test_filter_equipment_by_status(
        self, authenticated_student_client, sample_equipment, maintenance_equipment
    ):
        """Test filtering equipment by status."""
        url = reverse('equipment:equipment-list')
        response = authenticated_student_client.get(url, {'status': 'AVAILABLE'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['status'] == 'AVAILABLE'
    
    def test_filter_equipment_by_type(
        self, authenticated_student_client, sample_equipment, maintenance_equipment
    ):
        """Test filtering equipment by equipment_type."""
        url = reverse('equipment:equipment-list')
        response = authenticated_student_client.get(url, {'equipment_type': '3D Printer'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['equipment_type'] == '3D Printer'
    
    def test_search_equipment_by_name(self, authenticated_student_client, sample_equipment):
        """Test searching equipment by name."""
        url = reverse('equipment:equipment-list')
        response = authenticated_student_client.get(url, {'search': 'Alpha'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestEquipmentDetailAPI:
    """Test suite for equipment detail endpoint."""
    
    def test_retrieve_equipment_authenticated(self, authenticated_student_client, sample_equipment):
        """Test retrieving equipment detail with authenticated user."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == sample_equipment.name
        assert response.data['equipment_type'] == sample_equipment.equipment_type
        assert 'is_available' in response.data
        assert response.data['is_available'] is True
    
    def test_retrieve_equipment_unauthenticated(self, api_client, sample_equipment):
        """Test retrieving equipment fails for unauthenticated user."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_retrieve_nonexistent_equipment(self, authenticated_student_client):
        """Test retrieving non-existent equipment returns 404."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': 9999})
        response = authenticated_student_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestEquipmentCreateAPI:
    """Test suite for equipment creation endpoint."""
    
    def test_create_equipment_as_admin(self, authenticated_admin_client):
        """Test creating equipment as admin user."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'New Equipment',
            'description': 'New Description',
            'equipment_type': 'New Type',
            'location': 'New Location',
            'status': 'AVAILABLE',
            'max_booking_duration': 3
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['equipment']['name'] == 'New Equipment'
        assert Equipment.objects.filter(name='New Equipment').exists()
    
    def test_create_equipment_as_student_fails(self, authenticated_student_client):
        """Test creating equipment as student fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'New Equipment',
            'equipment_type': 'Type',
            'location': 'Location',
            'max_booking_duration': 3
        }
        response = authenticated_student_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_equipment_as_faculty_fails(self, authenticated_faculty_client):
        """Test creating equipment as faculty fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'New Equipment',
            'equipment_type': 'Type',
            'location': 'Location',
            'max_booking_duration': 3
        }
        response = authenticated_faculty_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_equipment_with_empty_name(self, authenticated_admin_client):
        """Test creating equipment with empty name fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': '',
            'equipment_type': 'Type',
            'location': 'Location',
            'max_booking_duration': 3
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
    
    def test_create_equipment_with_empty_type(self, authenticated_admin_client):
        """Test creating equipment with empty type fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'Name',
            'equipment_type': '',
            'location': 'Location',
            'max_booking_duration': 3
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'equipment_type' in response.data
    
    def test_create_equipment_with_empty_location(self, authenticated_admin_client):
        """Test creating equipment with empty location fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'Name',
            'equipment_type': 'Type',
            'location': '',
            'max_booking_duration': 3
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'location' in response.data
    
    def test_create_equipment_with_zero_max_duration(self, authenticated_admin_client):
        """Test creating equipment with zero max_booking_duration fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'Name',
            'equipment_type': 'Type',
            'location': 'Location',
            'max_booking_duration': 0
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'max_booking_duration' in response.data
    
    def test_create_equipment_with_negative_max_duration(self, authenticated_admin_client):
        """Test creating equipment with negative max_booking_duration fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'Name',
            'equipment_type': 'Type',
            'location': 'Location',
            'max_booking_duration': -1
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_equipment_with_invalid_status(self, authenticated_admin_client):
        """Test creating equipment with invalid status fails."""
        url = reverse('equipment:equipment-list')
        data = {
            'name': 'Name',
            'equipment_type': 'Type',
            'location': 'Location',
            'max_booking_duration': 3,
            'status': 'INVALID_STATUS'
        }
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.data


@pytest.mark.django_db
class TestEquipmentUpdateAPI:
    """Test suite for equipment update endpoint."""
    
    def test_update_equipment_as_admin(self, authenticated_admin_client, sample_equipment):
        """Test updating equipment as admin user."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        data = {
            'name': 'Updated Name',
            'equipment_type': 'Updated Type',
            'location': 'Updated Location',
            'max_booking_duration': 5
        }
        response = authenticated_admin_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['equipment']['name'] == 'Updated Name'
        
        sample_equipment.refresh_from_db()
        assert sample_equipment.name == 'Updated Name'
    
    def test_partial_update_equipment_as_admin(self, authenticated_admin_client, sample_equipment):
        """Test partial updating equipment as admin user."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        data = {'status': 'MAINTENANCE'}
        response = authenticated_admin_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['equipment']['status'] == 'MAINTENANCE'
        
        sample_equipment.refresh_from_db()
        assert sample_equipment.status == Equipment.Status.MAINTENANCE
    
    def test_update_equipment_as_student_fails(self, authenticated_student_client, sample_equipment):
        """Test updating equipment as student fails."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        data = {'name': 'Updated Name'}
        response = authenticated_student_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_equipment_as_faculty_fails(self, authenticated_faculty_client, sample_equipment):
        """Test updating equipment as faculty fails."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        data = {'name': 'Updated Name'}
        response = authenticated_faculty_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEquipmentDeleteAPI:
    """Test suite for equipment deletion endpoint."""
    
    def test_delete_equipment_as_admin(self, authenticated_admin_client, sample_equipment):
        """Test deleting equipment as admin user."""
        equipment_id = sample_equipment.id
        url = reverse('equipment:equipment-detail', kwargs={'pk': equipment_id})
        response = authenticated_admin_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert not Equipment.objects.filter(id=equipment_id).exists()
    
    def test_delete_equipment_as_student_fails(self, authenticated_student_client, sample_equipment):
        """Test deleting equipment as student fails."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        response = authenticated_student_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Equipment.objects.filter(id=sample_equipment.id).exists()
    
    def test_delete_equipment_as_faculty_fails(self, authenticated_faculty_client, sample_equipment):
        """Test deleting equipment as faculty fails."""
        url = reverse('equipment:equipment-detail', kwargs={'pk': sample_equipment.id})
        response = authenticated_faculty_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Equipment.objects.filter(id=sample_equipment.id).exists()
