/**
 * Equipment Page
 * Enhanced equipment browsing with search, filters, and booking
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import BookingModal from '../components/BookingModal';
import WaitingListModal from '../components/WaitingListModal';
import '../styles/Pages.css';

const Equipment = () => {
  const { user } = useAuth();
  const [equipment, setEquipment] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  
  // Modals
  const [bookingModal, setBookingModal] = useState({ isOpen: false, equipment: null });
  const [waitingListModal, setWaitingListModal] = useState({ 
    isOpen: false, 
    equipment: null, 
    conflictDetails: null 
  });
  
  // Success/notification messages
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchEquipment();
  }, []);

  const fetchEquipment = async () => {
    try {
      setLoading(true);
      const response = await api.get('/equipment/');
      setEquipment(response.data.results || response.data);
      setError('');
    } catch (err) {
      setError('Failed to load equipment. Please try again.');
      console.error('Error fetching equipment:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEquipment = equipment.filter(item => {
    const matchesSearch = !searchTerm || 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.location.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || item.status === statusFilter;
    
    const matchesType = typeFilter === 'ALL' || item.equipment_type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  const getUniqueTypes = () => {
    const types = [...new Set(equipment.map(item => item.equipment_type))];
    return types.sort();
  };

  const handleBookEquipment = (equipmentItem) => {
    setBookingModal({ isOpen: true, equipment: equipmentItem });
  };

  const handleBookingSuccess = (bookingData) => {
    setMessage(`Booking created successfully! Booking ID: #${bookingData.booking.id}`);
    setTimeout(() => setMessage(''), 5000);
    fetchEquipment(); // Refresh equipment status
  };

  const handleBookingError = (errorData, equipmentItem) => {
    // If it's a booking conflict, show waiting list option
    if (errorData.error === 'BOOKING_CONFLICT' || errorData.error === 'MAINTENANCE_CONFLICT') {
      setWaitingListModal({
        isOpen: true,
        equipment: equipmentItem,
        conflictDetails: {
          conflict_type: errorData.error === 'MAINTENANCE_CONFLICT' ? 'maintenance' : 'booking',
          start_time: errorData.requested_start_time,
          end_time: errorData.requested_end_time,
          conflict_start: errorData.conflict_start_time,
          conflict_end: errorData.conflict_end_time,
          maintenance_reason: errorData.maintenance_reason
        }
      });
    }
  };

  const handleWaitingListJoin = (waitingListData) => {
    setMessage(`Successfully joined waiting list! You are #${waitingListData.position} in line.`);
    setTimeout(() => setMessage(''), 5000);
  };

  const clearMessage = () => setMessage('');

  const getStatusInfo = (equipmentItem) => {
    switch (equipmentItem.status) {
      case 'AVAILABLE':
        return { text: 'Available', icon: '✅', color: '#155724' };
      case 'MAINTENANCE':
        return { text: 'Under Maintenance', icon: '🔧', color: '#856404' };
      case 'DISABLED':
        return { text: 'Disabled', icon: '❌', color: '#721c24' };
      default:
        return { text: equipmentItem.status, icon: '❓', color: '#666' };
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading equipment...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-state">
          {error}
          <button className="btn-secondary" onClick={fetchEquipment} style={{ marginTop: '15px' }}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Equipment</h1>
          <p>Browse and book available equipment</p>
        </div>
        <button className="btn-secondary" onClick={fetchEquipment}>
          Refresh
        </button>
      </div>

      {message && (
        <div className="success-message">
          {message}
          <button className="close-message" onClick={clearMessage}>×</button>
        </div>
      )}

      {/* Search and Filters */}
      <div className="equipment-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search equipment..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            <option value="ALL">All Status</option>
            <option value="AVAILABLE">Available</option>
            <option value="MAINTENANCE">Maintenance</option>
            <option value="DISABLED">Disabled</option>
          </select>
        </div>

        <div className="filter-group">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="filter-select"
          >
            <option value="ALL">All Types</option>
            {getUniqueTypes().map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      </div>

      {filteredEquipment.length === 0 ? (
        <div className="empty-state">
          <p>No equipment found matching your criteria.</p>
          {(searchTerm || statusFilter !== 'ALL' || typeFilter !== 'ALL') && (
            <button 
              className="btn-secondary"
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('ALL');
                setTypeFilter('ALL');
              }}
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="results-summary">
            Showing {filteredEquipment.length} of {equipment.length} equipment
          </div>

          <div className="equipment-grid">
            {filteredEquipment.map((item) => {
              const statusInfo = getStatusInfo(item);
              const isBookable = item.status === 'AVAILABLE';
              
              return (
                <div key={item.id} className="equipment-card enhanced">
                  <div className="equipment-header">
                    <h3>{item.name}</h3>
                    <div className="status-container">
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: statusInfo.color + '20', color: statusInfo.color }}
                      >
                        {statusInfo.icon} {statusInfo.text}
                      </span>
                    </div>
                  </div>

                  <div className="equipment-body">
                    <p className="equipment-type">{item.equipment_type}</p>
                    <p className="equipment-location">📍 {item.location}</p>
                    <p className="equipment-description">{item.description}</p>
                    
                    <div className="equipment-specs">
                      <div className="spec-item">
                        <span className="spec-label">Max Duration:</span>
                        <span className="spec-value">{item.max_booking_duration}h</span>
                      </div>
                    </div>
                  </div>

                  <div className="equipment-footer">
                    {!isBookable && (
                      <div className="unavailable-reason">
                        {item.status === 'MAINTENANCE' && (
                          <span>Equipment is under maintenance</span>
                        )}
                        {item.status === 'DISABLED' && (
                          <span>Equipment is currently disabled</span>
                        )}
                      </div>
                    )}
                    
                    <div className="equipment-actions">
                      <button 
                        className={`btn-primary ${!isBookable ? 'btn-disabled' : ''}`}
                        onClick={() => handleBookEquipment(item)}
                        disabled={!isBookable}
                      >
                        {isBookable ? 'Book Now' : 'Unavailable'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Booking Modal */}
      <BookingModal
        isOpen={bookingModal.isOpen}
        onClose={() => setBookingModal({ isOpen: false, equipment: null })}
        equipment={bookingModal.equipment}
        onBookingSuccess={handleBookingSuccess}
        onBookingError={handleBookingError}
      />

      {/* Waiting List Modal */}
      <WaitingListModal
        isOpen={waitingListModal.isOpen}
        onClose={() => setWaitingListModal({ isOpen: false, equipment: null, conflictDetails: null })}
        equipment={waitingListModal.equipment}
        conflictDetails={waitingListModal.conflictDetails}
        onWaitingListJoin={handleWaitingListJoin}
      />
    </div>
  );
};

export default Equipment;
