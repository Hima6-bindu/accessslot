/**
 * Booking Details Modal
 * Displays complete booking information
 */
import { useState } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import '../styles/Modal.css';

const BookingDetailsModal = ({ isOpen, onClose, booking, onBookingUpdate }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [cancellationReason, setCancellationReason] = useState('');

  if (!isOpen || !booking) return null;

  const canCancel = () => {
    return (
      booking.status === 'CONFIRMED' &&
      (user?.username === booking.user_username || user?.role === 'ADMIN') &&
      new Date(booking.start_time) > new Date()
    );
  };

  const handleCancelBooking = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.post(`/bookings/${booking.id}/cancel/`, {
        cancellation_reason: cancellationReason.trim() || 'Cancelled by user'
      });

      // Show waiting list notification if any
      if (response.data.waiting_list_notification?.notified) {
        // You could show a toast notification here
        console.log('Waiting list notification:', response.data.waiting_list_notification);
      }

      onBookingUpdate(response.data.booking);
      onClose();
    } catch (err) {
      const errorData = err.response?.data;
      setError(errorData?.detail || 'Failed to cancel booking. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'CONFIRMED': return '#155724';
      case 'CANCELLED': return '#721c24';
      case 'COMPLETED': return '#0c5460';
      case 'NO_SHOW': return '#856404';
      default: return '#666';
    }
  };

  const formatDuration = (hours) => {
    if (hours >= 24) {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
    }
    return `${hours}h`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Booking Details</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="booking-details">
            <div className="detail-section">
              <h3>Equipment Information</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <label>Equipment:</label>
                  <span>{booking.equipment_name}</span>
                </div>
                <div className="detail-item">
                  <label>Type:</label>
                  <span>{booking.equipment_type}</span>
                </div>
                {booking.equipment_location && (
                  <div className="detail-item">
                    <label>Location:</label>
                    <span>📍 {booking.equipment_location}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="detail-section">
              <h3>Booking Information</h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <label>Booking ID:</label>
                  <span>#{booking.id}</span>
                </div>
                <div className="detail-item">
                  <label>Status:</label>
                  <span 
                    className="status-badge" 
                    style={{ backgroundColor: getStatusColor(booking.status) + '20', color: getStatusColor(booking.status) }}
                  >
                    {booking.status}
                  </span>
                </div>
                <div className="detail-item full-width">
                  <label>Start Time:</label>
                  <span>{new Date(booking.start_time).toLocaleString()}</span>
                </div>
                <div className="detail-item full-width">
                  <label>End Time:</label>
                  <span>{new Date(booking.end_time).toLocaleString()}</span>
                </div>
                <div className="detail-item">
                  <label>Duration:</label>
                  <span>{formatDuration(booking.duration_hours)}</span>
                </div>
                <div className="detail-item">
                  <label>Created:</label>
                  <span>{new Date(booking.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>

            {booking.user_username !== user?.username && (
              <div className="detail-section">
                <h3>User Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>User:</label>
                    <span>{booking.user_username}</span>
                  </div>
                  {booking.user_email && (
                    <div className="detail-item">
                      <label>Email:</label>
                      <span>{booking.user_email}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {booking.cancellation_reason && (
              <div className="detail-section">
                <h3>Cancellation</h3>
                <div className="detail-item full-width">
                  <label>Reason:</label>
                  <span>{booking.cancellation_reason}</span>
                </div>
              </div>
            )}
          </div>

          {!showCancelConfirm && canCancel() && (
            <div className="booking-actions">
              <button 
                className="btn-danger" 
                onClick={() => setShowCancelConfirm(true)}
                disabled={loading}
              >
                Cancel Booking
              </button>
            </div>
          )}

          {showCancelConfirm && (
            <div className="cancel-confirmation">
              <h4>Cancel Booking</h4>
              <p>Are you sure you want to cancel this booking? This action cannot be undone.</p>
              
              <div className="form-group">
                <label htmlFor="cancellation_reason">Reason (optional):</label>
                <textarea
                  id="cancellation_reason"
                  value={cancellationReason}
                  onChange={(e) => setCancellationReason(e.target.value)}
                  placeholder="Enter reason for cancellation"
                  maxLength={500}
                  disabled={loading}
                />
              </div>

              <div className="cancel-actions">
                <button 
                  className="btn-secondary" 
                  onClick={() => setShowCancelConfirm(false)}
                  disabled={loading}
                >
                  Keep Booking
                </button>
                <button 
                  className="btn-danger" 
                  onClick={handleCancelBooking}
                  disabled={loading}
                >
                  {loading ? 'Cancelling...' : 'Confirm Cancellation'}
                </button>
              </div>
            </div>
          )}

          {!showCancelConfirm && (
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BookingDetailsModal;