"""
Tests for Equipment model.
"""
import pytest
from django.core.exceptions import ValidationError
from equipment.models import Equipment


@pytest.mark.django_db
class TestEquipmentModel:
    """Test suite for Equipment model."""
    
    def test_create_equipment_with_valid_data(self):
        """Test creating equipment with valid data."""
        equipment = Equipment.objects.create(
            name='Test Equipment',
            description='Test description',
            equipment_type='Test Type',
            location='Test Location',
            status=Equipment.Status.AVAILABLE,
            max_booking_duration=5
        )
        
        assert equipment.name == 'Test Equipment'
        assert equipment.equipment_type == 'Test Type'
        assert equipment.location == 'Test Location'
        assert equipment.status == Equipment.Status.AVAILABLE
        assert equipment.max_booking_duration == 5
        assert equipment.is_available is True
        assert equipment.is_under_maintenance is False
        assert equipment.is_disabled is False
    
    def test_equipment_default_status(self):
        """Test equipment default status is AVAILABLE."""
        equipment = Equipment.objects.create(
            name='Test Equipment',
            equipment_type='Test Type',
            location='Test Location',
            max_booking_duration=3
        )
        
        assert equipment.status == Equipment.Status.AVAILABLE
    
    def test_equipment_status_choices(self):
        """Test all status choices are valid."""
        statuses = [Equipment.Status.AVAILABLE, Equipment.Status.MAINTENANCE, Equipment.Status.DISABLED]
        
        for status in statuses:
            equipment = Equipment.objects.create(
                name=f'Equipment {status}',
                equipment_type='Type',
                location='Location',
                status=status,
                max_booking_duration=2
            )
            assert equipment.status == status
    
    def test_equipment_string_representation(self):
        """Test __str__ method of Equipment model."""
        equipment = Equipment.objects.create(
            name='3D Printer',
            equipment_type='Printer',
            location='Lab 1',
            max_booking_duration=4
        )
        
        assert str(equipment) == '3D Printer (Printer)'
    
    def test_equipment_status_properties(self):
        """Test status helper properties."""
        # Test AVAILABLE
        available_eq = Equipment.objects.create(
            name='Available Equipment',
            equipment_type='Type',
            location='Location',
            status=Equipment.Status.AVAILABLE,
            max_booking_duration=2
        )
        assert available_eq.is_available is True
        assert available_eq.is_under_maintenance is False
        assert available_eq.is_disabled is False
        
        # Test MAINTENANCE
        maintenance_eq = Equipment.objects.create(
            name='Maintenance Equipment',
            equipment_type='Type',
            location='Location',
            status=Equipment.Status.MAINTENANCE,
            max_booking_duration=2
        )
        assert maintenance_eq.is_available is False
        assert maintenance_eq.is_under_maintenance is True
        assert maintenance_eq.is_disabled is False
        
        # Test DISABLED
        disabled_eq = Equipment.objects.create(
            name='Disabled Equipment',
            equipment_type='Type',
            location='Location',
            status=Equipment.Status.DISABLED,
            max_booking_duration=2
        )
        assert disabled_eq.is_available is False
        assert disabled_eq.is_under_maintenance is False
        assert disabled_eq.is_disabled is True
    
    def test_equipment_name_validation(self):
        """Test name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Equipment.objects.create(
                name='',
                equipment_type='Type',
                location='Location',
                max_booking_duration=2
            )
        
        assert 'name' in exc_info.value.message_dict
    
    def test_equipment_name_whitespace_validation(self):
        """Test name cannot be whitespace only."""
        with pytest.raises(ValidationError) as exc_info:
            Equipment.objects.create(
                name='   ',
                equipment_type='Type',
                location='Location',
                max_booking_duration=2
            )
        
        assert 'name' in exc_info.value.message_dict
    
    def test_equipment_type_validation(self):
        """Test equipment_type cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Equipment.objects.create(
                name='Name',
                equipment_type='',
                location='Location',
                max_booking_duration=2
            )
        
        assert 'equipment_type' in exc_info.value.message_dict
    
    def test_equipment_location_validation(self):
        """Test location cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Equipment.objects.create(
                name='Name',
                equipment_type='Type',
                location='',
                max_booking_duration=2
            )
        
        assert 'location' in exc_info.value.message_dict
    
    def test_max_booking_duration_positive_validation(self):
        """Test max_booking_duration must be greater than 0."""
        with pytest.raises(ValidationError) as exc_info:
            Equipment.objects.create(
                name='Name',
                equipment_type='Type',
                location='Location',
                max_booking_duration=0
            )
        
        assert 'max_booking_duration' in exc_info.value.message_dict
    
    def test_max_booking_duration_negative_validation(self):
        """Test max_booking_duration cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            Equipment.objects.create(
                name='Name',
                equipment_type='Type',
                location='Location',
                max_booking_duration=-1
            )
        
        assert 'max_booking_duration' in exc_info.value.message_dict
    
    def test_equipment_ordering(self):
        """Test equipment is ordered by name."""
        Equipment.objects.create(name='Zebra', equipment_type='Type', location='Loc', max_booking_duration=1)
        Equipment.objects.create(name='Alpha', equipment_type='Type', location='Loc', max_booking_duration=1)
        Equipment.objects.create(name='Beta', equipment_type='Type', location='Loc', max_booking_duration=1)
        
        equipment_list = list(Equipment.objects.all())
        assert equipment_list[0].name == 'Alpha'
        assert equipment_list[1].name == 'Beta'
        assert equipment_list[2].name == 'Zebra'
    
    def test_equipment_timestamps(self):
        """Test created_at and updated_at timestamps."""
        equipment = Equipment.objects.create(
            name='Test Equipment',
            equipment_type='Type',
            location='Location',
            max_booking_duration=2
        )
        
        assert equipment.created_at is not None
        assert equipment.updated_at is not None
        assert equipment.created_at <= equipment.updated_at
