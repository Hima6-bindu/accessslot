/**
 * Waiting List Modal
 * Allows users to join waiting list when equipment is unavailable
 */
import { useState } from 'react';
import api from '../services/api';
import '../styles/Modal.css';

const WaitingListModal = ({ isOpen, onClose, equipment, conflictDetails, onWaitingListJoin }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleJoinWaitingList = async () => {
    if (!conflictDetails) return;

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/waiting-list/join/', {
        equipment: equipment.id,
        requested_start_time: conflictDetails.start_time,
        requested_end_time: conflictDetails.end_time
      });

      onWaitingListJoin(response.data);
      onClose();
    } catch (err) {
      const errorData = err.response?.data;
      
      if (errorData?.non_field_errors) {
        setError(errorData.non_field_errors.join(', '));
      } else if (typeof errorData === 'object') {
        const errors = Object.entries(errorData)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('\n');
        setError(errors);
      } else {
        setError('Failed to join waiting list. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !equipment || !conflictDetails) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Equipment Unavailable</h2>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="conflict-info">
            <h3>Booking Conflict</h3>
            <p>The requested time slot for <strong>{equipment.name}</strong> is not available due to:</p>
            
            {conflictDetails.conflict_type === 'booking' && (
              <div className="conflict-details">
                <p>🗓️ <strong>Existing Booking</strong></p>
                <p>Conflicting time: {new Date(conflictDetails.conflict_start).toLocaleString()} - {new Date(conflictDetails.conflict_end).toLocaleString()}</p>
              </div>
            )}

            {conflictDetails.conflict_type === 'maintenance' && (
              <div className="conflict-details">
                <p>🔧 <strong>Scheduled Maintenance</strong></p>
                <p>Maintenance period: {new Date(conflictDetails.conflict_start).toLocaleString()} - {new Date(conflictDetails.conflict_end).toLocaleString()}</p>
                <p>Reason: {conflictDetails.maintenance_reason}</p>
              </div>
            )}
          </div>

          <div className="waiting-list-option">
            <h4>Join Waiting List</h4>
            <p>Would you like to join the waiting list for this time slot? You'll be notified if the equipment becomes available.</p>
            
            <div className="requested-time">
              <p><strong>Requested Time:</strong></p>
              <p>{new Date(conflictDetails.start_time).toLocaleString()} - {new Date(conflictDetails.end_time).toLocaleString()}</p>
            </div>

            {error && (
              <div className="error-message">{error}</div>
            )}
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button 
              type="button" 
              className="btn-primary" 
              onClick={handleJoinWaitingList} 
              disabled={loading}
            >
              {loading ? 'Joining...' : 'Join Waiting List'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WaitingListModal;