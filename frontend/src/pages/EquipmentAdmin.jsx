/**
 * Equipment Management (Admin)
 * Complete CRUD interface for equipment
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import '../styles/Pages.css';
import '../styles/Admin.css';

const EquipmentAdmin = () => {
  const [equipment, setEquipment] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEquipment, setEditingEquipment] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    equipment_type: '',
    location: '',
    status: 'AVAILABLE',
    max_booking_duration: 4
  });
  const [submitting, setSubmitting] = useState(false);

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
      setError('Failed to load equipment.');
      console.error('Error fetching equipment:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEquipment = equipment.filter(item => {
    const matchesSearch = !searchTerm || 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'ALL' || item.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const handleCreate = () => {
    setEditingEquipment(null);
    setFormData({
      name: '',
      description: '',
      equipment_type: '',
      location: '',
      status: 'AVAILABLE',
      max_booking_duration: 4
    });
    setModalOpen(true);
  };

  const handleEdit = (item) => {
    setEditingEquipment(item);
    setFormData({
      name: item.name,
      description: item.description,
      equipment_type: item.equipment_type,
      location: item.location,
      status: item.status,
      max_booking_duration: item.max_booking_duration
    });
    setModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (!window.confirm(`Are you sure you want to delete "${item.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await api.delete(`/equipment/${item.id}/`);
      setMessage(`Equipment "${item.name}" deleted successfully.`);
      setTimeout(() => setMessage(''), 5000);
      fetchEquipment();
    } catch (err) {
      const errorData = err.response?.data;
      setError(errorData?.detail || 'Failed to delete equipment.');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      if (editingEquipment) {
        // Update existing
        await api.patch(`/equipment/${editingEquipment.id}/`, formData);
        setMessage('Equipment updated successfully.');
      } else {
        // Create new
        await api.post('/equipment/', formData);
        setMessage('Equipment created successfully.');
      }
      
      setTimeout(() => setMessage(''), 5000);
      setModalOpen(false);
      fetchEquipment();
    } catch (err) {
      const errorData = err.response?.data;
      if (typeof errorData === 'object') {
        const errors = Object.entries(errorData)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
          .join('\n');
        setError(errors);
      } else {
        setError('Failed to save equipment.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'max_booking_duration' ? parseInt(value) || 0 : value
    }));
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading equipment...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Equipment Management</h1>
          <p>Manage all equipment in the system</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={fetchEquipment}>
            Refresh
          </button>
          <button className="btn-primary" onClick={handleCreate}>
            + Add Equipment
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

      {/* Filters */}
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
      </div>

      {filteredEquipment.length === 0 ? (
        <div className="empty-state">
          <p>No equipment found.</p>
          <button className="btn-primary" onClick={handleCreate}>
            Add Equipment
          </button>
        </div>
      ) : (
        <>
          <div className="results-summary">
            Showing {filteredEquipment.length} of {equipment.length} equipment
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Status</th>
                  <th>Max Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredEquipment.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.name}</strong>
                      <div className="item-description">{item.description}</div>
                    </td>
                    <td>{item.equipment_type}</td>
                    <td>📍 {item.location}</td>
                    <td>
                      <span className={`status-badge status-${item.status.toLowerCase()}`}>
                        {item.status}
                      </span>
                    </td>
                    <td>{item.max_booking_duration}h</td>
                    <td>
                      <div className="table-actions">
                        <button 
                          className="btn-small"
                          onClick={() => handleEdit(item)}
                        >
                          Edit
                        </button>
                        <button 
                          className="btn-small btn-danger"
                          onClick={() => handleDelete(item)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Equipment Form Modal */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingEquipment ? 'Edit Equipment' : 'Add Equipment'}</h2>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>

            <div className="modal-body">
              <form onSubmit={handleSubmit}>
                {error && (
                  <div className="error-message">{error}</div>
                )}

                <div className="form-group">
                  <label htmlFor="name">Name *</label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">Description *</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    required
                    disabled={submitting}
                    rows={3}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="equipment_type">Equipment Type *</label>
                    <input
                      id="equipment_type"
                      name="equipment_type"
                      type="text"
                      value={formData.equipment_type}
                      onChange={handleChange}
                      required
                      disabled={submitting}
                      placeholder="e.g., MICROSCOPE, PRINTER_3D"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="location">Location *</label>
                    <input
                      id="location"
                      name="location"
                      type="text"
                      value={formData.location}
                      onChange={handleChange}
                      required
                      disabled={submitting}
                      placeholder="e.g., Lab 101"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="status">Status *</label>
                    <select
                      id="status"
                      name="status"
                      value={formData.status}
                      onChange={handleChange}
                      required
                      disabled={submitting}
                    >
                      <option value="AVAILABLE">Available</option>
                      <option value="MAINTENANCE">Maintenance</option>
                      <option value="DISABLED">Disabled</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="max_booking_duration">Max Booking Duration (hours) *</label>
                    <input
                      id="max_booking_duration"
                      name="max_booking_duration"
                      type="number"
                      value={formData.max_booking_duration}
                      onChange={handleChange}
                      required
                      disabled={submitting}
                      min="1"
                      max="168"
                    />
                  </div>
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
                    {submitting ? 'Saving...' : (editingEquipment ? 'Update' : 'Create')}
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

export default EquipmentAdmin;