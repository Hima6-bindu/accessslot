/**
 * Booking Creation Modal
 * Complete form for creating equipment bookings
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import '../styles/Modal.css';

const BookingModal = ({ isOpen, onClose, equipment, onBookingSuccess, onBookingError }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    start_date: '',
    start_time: '',
    end_date: '',
    end_time: '',
    purpose: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userStats, setUserStats] = useState(null);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen && equipment) {
      // Set default dates to today
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      setFormData({
        start_date: today.toISOString().split('T')[0],
        start_time: '09:00',
        end_date: today.toISOString().split('T')[0],
        end_time: '11:00',
        purpose: ''
      });
      setError('');
      fetchUserStats();
    }
  }, [isOpen, equipment]);

  const fetchUserStats = async () => {
    try {
      // This would be a real endpoint in the backend
      // For now, we'll use placeholder data
      setUserStats({
        weekly_hours_used: 5,
        weekly_limit: 20
      });
    } catch (err) {
      console.error('Failed to fetch user stats:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getDuration = () => {
    if (!formData.start_date || !formData.start_time || !formData.end_date || !formData.end_time) {
      return 0;
    }

    const startDateTime = new Date(`${formData.start_date}T${formData.start_time}`);
    const endDateTime = new Date(`${formData.end_date}T${formData.end_time}`);
    
    const diffMs = endDateTime - startDateTime;
    const diffHours = diffMs / (1000 * 60 * 60);
    
    return Math.max(0, diffHours);
  };

  const validateForm = () => {
    const duration = getDuration();
    
    if (duration <= 0) {
      return 'End time must be after start time';
    }

    if (duration > equipment?.max_booking_duration) {
      return `Duration (${duration.toFixed(1)}h) exceeds equipment maximum (${equipment.max_booking_duration}h)`;
    }

    const startDateTime = new Date(`${formData.start_date}T${formData.start_time}`);
    if (startDateTime < new Date()) {
      return 'Booking cannot be in the past';
    }

    if (!formData.purpose.trim()) {
      return 'Purpose is required';
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const startDateTime = new Date(`${formData.start_date}T${formData.start_time}`);
      const endDateTime = new Date(`${formData.end_date}T${formData.end_time}`);

      const response = await api.post('/bookings/', {
        equipment: equipment.id,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString()
      });

      onBookingSuccess(response.data);
      onClose();
    } catch (err) {
      const errorData = err.response?.data;
      
      if (errorData?.error === 'BOOKING_CONFLICT') {
        // Close booking modal and show waiting list option
        onClose();
        if (onBookingError) {
          onBookingError({
            ...errorData,
            requested_start_time: new Date(`${formData.start_date}T${formData.start_time}`).toISOString(),
            requested_end_time: new Date(`${formData.end_date}T${formData.end_time}`).toISOString()
          }, equipment);
        }
        return;
      } else if (errorData?.error === 'MAINTENANCE_CONFLICT') {
        // Close booking modal and show waiting list option
        onClose();
        if (onBookingError) {
          onBookingError({
            ...errorData,
            requested_start_time: new Date(`${formData.start_date}T${formData.start_time}`).toISOString(),
            requested_end_time: new Date(`${formData.end_date}T${formData.end_time}`).toISOString()
          }, equipment);
        }
        return;
      } else if (errorData?.error === 'WEEKLY_LIMIT_EXCEEDED') {
        setError(`Weekly limit exceeded: ${errorData.message}`);
      } else if (errorData?.non_field_errors) {
        setError(errorData.non_field_errors.join(', '));
      } else if (typeof errorData === 'object') {
        const errors = Object.entries(errorData)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('\n');
        setError(errors);
      } else {
        setError('Failed to create booking. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !equipment) return null;

  const duration = getDuration();
  const remainingWeeklyHours = userStats ? userStats.weekly_limit - userStats.weekly_hours_used : 0;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Book Equipment</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="booking-equipment-info">
            <h3>{equipment.name}</h3>
            <p className="equipment-type">{equipment.equipment_type}</p>
            <p className="equipment-location">📍 {equipment.location}</p>
            <p className="equipment-max-duration">
              Maximum booking: {equipment.max_booking_duration} hours
            </p>
          </div>

          {userStats && (
            <div className="user-stats">
              <h4>Your Weekly Usage</h4>
              <div className="stats-bar">
                <div className="stats-used" style={{ width: `${(userStats.weekly_hours_used / userStats.weekly_limit) * 100}%` }}></div>
              </div>
              <p>{userStats.weekly_hours_used}h / {userStats.weekly_limit}h used</p>
              <p>Remaining: {remainingWeeklyHours}h</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="booking-form">
            {error && (
              <div className="error-message">{error}</div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start_date">Start Date</label>
                <input
                  id="start_date"
                  name="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                  disabled={loading}
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label htmlFor="start_time">Start Time</label>
                <input
                  id="start_time"
                  name="start_time"
                  type="time"
                  value={formData.start_time}
                  onChange={handleChange}
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="end_date">End Date</label>
                <input
                  id="end_date"
                  name="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={handleChange}
                  required
                  disabled={loading}
                  min={formData.start_date || new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label htmlFor="end_time">End Time</label>
                <input
                  id="end_time"
                  name="end_time"
                  type="time"
                  value={formData.end_time}
                  onChange={handleChange}
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="purpose">Purpose</label>
              <textarea
                id="purpose"
                name="purpose"
                value={formData.purpose}
                onChange={handleChange}
                placeholder="Describe how you plan to use this equipment"
                required
                disabled={loading}
                maxLength={500}
              />
            </div>

            <div className="booking-summary">
              <h4>Booking Summary</h4>
              <p><strong>Equipment:</strong> {equipment.name}</p>
              <p><strong>Duration:</strong> {duration.toFixed(1)} hours</p>
              {duration > 0 && (
                <>
                  <p><strong>Start:</strong> {new Date(`${formData.start_date}T${formData.start_time}`).toLocaleString()}</p>
                  <p><strong>End:</strong> {new Date(`${formData.end_date}T${formData.end_time}`).toLocaleString()}</p>
                </>
              )}
              {duration > equipment.max_booking_duration && (
                <p className="warning">⚠️ Duration exceeds equipment maximum</p>
              )}
            </div>

            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Creating booking...' : 'Create Booking'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default BookingModal;