/**
 * My Waiting List Page
 * Enhanced waiting list management with cancellation
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import '../styles/Pages.css';

const MyWaitingList = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [cancellingId, setCancellingId] = useState(null);

  useEffect(() => {
    fetchWaitingList();
  }, []);

  const fetchWaitingList = async () => {
    try {
      setLoading(true);
      const response = await api.get('/waiting-list/');
      setEntries(response.data.results || response.data);
      setError('');
    } catch (err) {
      setError('Failed to load waiting list.');
      console.error('Error fetching waiting list:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEntry = async (entryId) => {
    if (!window.confirm('Are you sure you want to cancel this waiting list entry?')) {
      return;
    }

    setCancellingId(entryId);
    
    try {
      await api.post(`/waiting-list/${entryId}/cancel/`);
      
      // Remove the entry from the list
      setEntries(prev => prev.filter(entry => entry.id !== entryId));
      setMessage('Waiting list entry cancelled successfully.');
      setTimeout(() => setMessage(''), 5000);
    } catch (err) {
      const errorData = err.response?.data;
      setError(errorData?.detail || 'Failed to cancel waiting list entry.');
      setTimeout(() => setError(''), 5000);
    } finally {
      setCancellingId(null);
    }
  };

  const getStatusInfo = (status) => {
    switch (status) {
      case 'WAITING':
        return { text: 'Waiting', icon: '⏳', color: '#084298', bgColor: '#cfe2ff' };
      case 'NOTIFIED':
        return { text: 'Notified', icon: '🔔', color: '#0c5460', bgColor: '#d1ecf1' };
      case 'CANCELLED':
        return { text: 'Cancelled', icon: '❌', color: '#721c24', bgColor: '#f8d7da' };
      case 'FULFILLED':
        return { text: 'Fulfilled', icon: '✅', color: '#155724', bgColor: '#d4edda' };
      default:
        return { text: status, icon: '❓', color: '#666', bgColor: '#f8f9fa' };
    }
  };

  const formatTimeRange = (startTime, endTime) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    
    const startStr = start.toLocaleDateString() + ' ' + start.toLocaleTimeString();
    const endStr = end.toLocaleDateString() + ' ' + end.toLocaleTimeString();
    
    // If same date, show date once
    if (start.toDateString() === end.toDateString()) {
      return `${start.toLocaleDateString()} ${start.toLocaleTimeString()} - ${end.toLocaleTimeString()}`;
    }
    
    return `${startStr} - ${endStr}`;
  };

  const canCancelEntry = (entry) => {
    return entry.status === 'WAITING' || entry.status === 'NOTIFIED';
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading waiting list...</div>
      </div>
    );
  }

  if (error && entries.length === 0) {
    return (
      <div className="page-container">
        <div className="error-state">
          {error}
          <button className="btn-secondary" onClick={fetchWaitingList} style={{ marginTop: '15px' }}>
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
          <h1>My Waiting List</h1>
          <p>Track your position in equipment waiting lists</p>
        </div>
        <button className="btn-secondary" onClick={fetchWaitingList}>
          Refresh
        </button>
      </div>

      {message && (
        <div className="success-message">
          {message}
          <button className="close-message" onClick={() => setMessage('')}>×</button>
        </div>
      )}

      {error && entries.length > 0 && (
        <div className="error-message" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {entries.length === 0 ? (
        <div className="empty-state">
          <p>You're not on any waiting lists.</p>
          <p>Join a waiting list when equipment becomes unavailable during booking.</p>
        </div>
      ) : (
        <>
          <div className="results-summary">
            {entries.length} waiting list {entries.length === 1 ? 'entry' : 'entries'}
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Equipment</th>
                  <th>Position</th>
                  <th>Requested Time</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const statusInfo = getStatusInfo(entry.status);
                  const isCancelling = cancellingId === entry.id;
                  
                  return (
                    <tr key={entry.id}>
                      <td>
                        <strong>{entry.equipment_name}</strong>
                      </td>
                      <td>
                        <span className="position-badge">
                          #{entry.position}
                        </span>
                      </td>
                      <td className="time-cell">
                        <div className="time-range">
                          {formatTimeRange(entry.requested_start_time, entry.requested_end_time)}
                        </div>
                      </td>
                      <td>
                        <span 
                          className="status-badge"
                          style={{ 
                            backgroundColor: statusInfo.bgColor, 
                            color: statusInfo.color 
                          }}
                        >
                          {statusInfo.icon} {statusInfo.text}
                        </span>
                      </td>
                      <td>
                        {new Date(entry.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div className="waiting-list-actions">
                          {canCancelEntry(entry) ? (
                            <button 
                              className="btn-small btn-danger"
                              onClick={() => handleCancelEntry(entry.id)}
                              disabled={isCancelling}
                            >
                              {isCancelling ? 'Cancelling...' : 'Cancel'}
                            </button>
                          ) : (
                            <span className="text-muted">-</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Status Legend */}
          <div className="status-legend">
            <h4>Status Legend:</h4>
            <div className="legend-grid">
              <div className="legend-item">
                <span className="status-badge" style={{ backgroundColor: '#cfe2ff', color: '#084298' }}>
                  ⏳ WAITING
                </span>
                <span>You're in the queue waiting for equipment to become available</span>
              </div>
              <div className="legend-item">
                <span className="status-badge" style={{ backgroundColor: '#d1ecf1', color: '#0c5460' }}>
                  🔔 NOTIFIED
                </span>
                <span>Equipment is available! Check your bookings to confirm</span>
              </div>
              <div className="legend-item">
                <span className="status-badge" style={{ backgroundColor: '#d4edda', color: '#155724' }}>
                  ✅ FULFILLED
                </span>
                <span>Your waiting list request has been fulfilled with a booking</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MyWaitingList;
