/**
 * Maintenance Page (Admin Only)
 * Manage equipment maintenance schedules with full CRUD
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import '../styles/Pages.css';
import '../styles/Admin.css';

const Maintenance = () => {
  const [maintenance, setMaintenance] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMaintenance, setEditingMaintenance] = useState(null);
  const [formData, setFormData] = useState({
    equipment: '',
    start_time: '',
    end_time: '',
    reason: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [maintenanceRes, equipmentRes] = await Promise.all([
        api.get('/maintenance/'),
        api.get('/equipment/')
      ]);
      
      setMaintenance(maintenanceRes.data.results || maintenanceRes.data);
      setEquipment(equipmentRes.data.results || equipmentRes.data);
      setError('');
    } catch (err) {
      setError('Failed to load maintenance records.');
      console.error('Error fetching maintenance:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMaintenanceStatus = (item) => {
    const now = new Date();
    const start = new Date(item.start_time);
    const end = new Date(item.end_time);
    
    if (end < now) return 'completed';
    if (start <= now && now <= end) return 'active';
    return 'upcoming';
  };

  const handleCreate = () => {
    setEditingMaintenance(null);
    setFormData({
      equipment: '',
      start_time: '',
      end_time: '',
      reason: ''
    });
    setModalOpen(true);
  };

  const handleEdit = (item) => {
    setEditingMaintenance(item);
    
    // Format datetime for input fields
    const startDate = new Date(item.start_time);
    const endDate = new Date(item.end_time);
    
    setFormData({
      equipment: item.equipment,
      start_time: startDate.toISOString().slice(0, 16),
      end_time: endDate.toISOString().slice(0, 16),
      reason: item.reason
    });
    setModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (!window.confirm(`Are you sure you want to delete this maintenance schedule? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.delete(`/maintenance/${item.id}/`);
      setMessage('Maintenance schedule deleted successfully.');
      setTimeout(() => setMessage(''), 5000);
      fetchData();
    } catch (err) {
      const errorData = err.response?.data;
      setError(errorData?.detail || 'Failed to delete maintenance schedule.');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const submitData = {
        equipment: parseInt(formData.equipment),
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        reason: formData.reason
      };

      if (editingMaintenance) {
        await api.patch(`/maintenance/${editingMaintenance.id}/`, submitData);
        setMessage('Maintenance schedule updated successfully.');
      } else {
        await api.post('/maintenance/', submitData);
        setMessage('Maintenance schedule created successfully.');
      }
      
      setTimeout(() => setMessage(''), 5000);
      setModalOpen(false);
      fetchData();
    } catch (err) {
      const errorData = err.response?.data;
      if (typeof errorData === 'object') {
        const errors = Object.entries(errorData)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('\n');
        setError(errors);
      } else {
        setError('Failed to save maintenance schedule.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading maintenance records...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Maintenance Management</h1>
          <p>Schedule and track equipment maintenance</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={fetchData}>
            Refresh
          </button>
          <button className="btn-primary" onClick={handleCreate}>
            + Schedule Maintenance
          </button>
        </div>
      </div>

      {message && (
        <div className="success-message">
          {message}
          <button className="close-message" onClick={() => setMessage('')}>×</button>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
          <button className="close-message" onClick={() => setError('')}>×</button>
        </div>
      )}

      {maintenance.length === 0 ? (
        <div className="empty-state">
          <p>No maintenance scheduled.</p>
          <button className="btn-primary" onClick={handleCreate}>
            Schedule Maintenance
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Equipment</th>
                <th>Start Time</th>
                <th>End Time</th>
                <th>Duration</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {maintenance.map((item) => {
                const status = getMaintenanceStatus(item);
                const duration = (new Date(item.end_time) - new Date(item.start_time)) / (1000 * 60 * 60);
                
                return (
                  <tr key={item.id} className={`maintenance-${status}`}>
                    <td>
                      <strong>{item.equipment_name}</strong>
                    </td>
                    <td>{new Date(item.start_time).toLocaleString()}</td>
                    <td>{new Date(item.end_time).toLocaleString()}</td>
                    <td>{duration.toFixed(1)}h</td>
                    <td className="purpose-text">{item.reason}</td>
                    <td>
                      <span className={`status-badge status-${status}`}>
                        {status === 'active' && '🔧 Active'}
                        {status === 'upcoming' && '📅 Upcoming'}
                        {status === 'completed' && '✅ Completed'}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        {status !== 'completed' && (
                          <button 
                            className="btn-small"
                            onClick={() => handleEdit(item)}
                          >
                            Edit
                          </button>
                        )}
                        <button 
                          className="btn-small btn-danger"
                          onClick={() => handleDelete(item)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Maintenance Form Modal */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingMaintenance ? 'Edit Maintenance' : 'Schedule Maintenance'}</h2>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>

            <div className="modal-body">
              <form onSubmit={handleSubmit}>
                {error && (
                  <div className="error-message">{error}</div>
                )}

                <div className="form-group">
                  <label htmlFor="equipment">Equipment *</label>
                  <select
                    id="equipment"
                    name="equipment"
                    value={formData.equipment}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                  >
                    <option value="">Select equipment</option>
                    {equipment.map(eq => (
                      <option key={eq.id} value={eq.id}>
                        {eq.name} - {eq.location}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="start_time">Start Time *</label>
                    <input
                      id="start_time"
                      name="start_time"
                      type="datetime-local"
                      value={formData.start_time}
                      onChange={handleChange}
                      required
                      disabled={submitting}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="end_time">End Time *</label>
                    <input
                      id="end_time"
                      name="end_time"
                      type="datetime-local"
                      value={formData.end_time}
                      onChange={handleChange}
                      required
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="reason">Reason *</label>
                  <textarea
                    id="reason"
                    name="reason"
                    value={formData.reason}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                    rows={4}
                    placeholder="Describe the maintenance work to be performed"
                  />
                </div>

                <div className="status-change-warning">
                  ⚠️ Note: Creating maintenance will make the equipment unavailable during the specified period. 
                  Existing confirmed bookings during this time will prevent maintenance creation.
                </div>

                <div className="modal-actions">
                  <button 
                    type="button" 
                    className="btn-secondary" 
                    onClick={() => setModalOpen(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="btn-primary"
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : (editingMaintenance ? 'Update' : 'Schedule')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Maintenance;
