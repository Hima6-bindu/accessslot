/**
 * Admin Users Page
 * Full user management with search, filters, and editing capabilities
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import '../styles/Pages.css';
import '../styles/Admin.css';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [activeFilter, setActiveFilter] = useState('ALL');
  
  // Edit modal state
  const [editingUser, setEditingUser] = useState(null);
  const [editFormData, setEditFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    role: '',
    is_active: true
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');
  const [showConfirmDeactivate, setShowConfirmDeactivate] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Build query params
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (roleFilter !== 'ALL') params.role = roleFilter;
      if (activeFilter !== 'ALL') params.is_active = activeFilter === 'ACTIVE' ? 'true' : 'false';
      
      const response = await api.get('/auth/users/', { params });
      setUsers(response.data);
    } catch (err) {
      setError('Failed to load users. ' + (err.response?.data?.detail || err.message));
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  // Apply filters when they change
  useEffect(() => {
    fetchUsers();
  }, [searchTerm, roleFilter, activeFilter]);

  const openEditModal = (user) => {
    setEditingUser(user);
    setEditFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email,
      role: user.role,
      is_active: user.is_active
    });
    setEditError('');
    setShowConfirmDeactivate(false);
  };

  const closeEditModal = () => {
    setEditingUser(null);
    setEditFormData({
      first_name: '',
      last_name: '',
      email: '',
      role: '',
      is_active: true
    });
    setEditError('');
    setShowConfirmDeactivate(false);
  };

  const handleEditFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    // If trying to deactivate, show confirmation
    if (editingUser.is_active && !editFormData.is_active && !showConfirmDeactivate) {
      setShowConfirmDeactivate(true);
      return;
    }
    
    try {
      setEditLoading(true);
      setEditError('');
      
      await api.patch(`/auth/users/${editingUser.id}/`, editFormData);
      
      setSuccess(`User ${editingUser.username} updated successfully`);
      setTimeout(() => setSuccess(''), 5000);
      
      closeEditModal();
      fetchUsers();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 
                       Object.values(err.response?.data || {}).flat().join(', ') ||
                       'Failed to update user';
      setEditError(errorMsg);
      console.error('Error updating user:', err);
    } finally {
      setEditLoading(false);
    }
  };

  const filteredUsers = users;

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading users...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>User Management</h1>
          <p>Manage system users and permissions</p>
        </div>
        <button className="btn-secondary" onClick={fetchUsers} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="equipment-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search by username, email, or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="filter-select"
          >
            <option value="ALL">All Roles</option>
            <option value="STUDENT">Students</option>
            <option value="FACULTY">Faculty</option>
            <option value="ADMIN">Admins</option>
          </select>
        </div>

        <div className="filter-group">
          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="filter-select"
          >
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Loading users...</div>
      ) : filteredUsers.length === 0 ? (
        <div className="empty-state">
          <p>No users found.</p>
          {(searchTerm || roleFilter !== 'ALL' || activeFilter !== 'ALL') && (
            <p>Try adjusting your filters.</p>
          )}
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Date Joined</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user) => (
                <tr key={user.id}>
                  <td><strong>{user.username}</strong></td>
                  <td>{user.first_name} {user.last_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`status-badge status-${user.role.toLowerCase()}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>{new Date(user.date_joined).toLocaleDateString()}</td>
                  <td>
                    <span className={`status-badge ${user.is_active ? 'status-available' : 'status-disabled'}`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="btn-small" 
                      onClick={() => openEditModal(user)}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit User: {editingUser.username}</h2>
              <button className="modal-close" onClick={closeEditModal}>×</button>
            </div>

            {editError && (
              <div className="error-message">
                {editError}
              </div>
            )}

            {showConfirmDeactivate ? (
              <div className="confirmation-dialog">
                <p className="warning-text">
                  <strong>⚠️ Confirm Deactivation</strong>
                </p>
                <p>
                  Are you sure you want to deactivate user <strong>{editingUser.username}</strong>?
                  This will prevent them from logging in and accessing the system.
                </p>
                <div className="modal-actions">
                  <button 
                    type="button" 
                    className="btn-secondary"
                    onClick={() => setShowConfirmDeactivate(false)}
                    disabled={editLoading}
                  >
                    Cancel
                  </button>
                  <button 
                    type="button" 
                    className="btn-danger"
                    onClick={handleEditSubmit}
                    disabled={editLoading}
                  >
                    {editLoading ? 'Deactivating...' : 'Confirm Deactivation'}
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleEditSubmit}>
                <div className="form-group">
                  <label>First Name</label>
                  <input
                    type="text"
                    name="first_name"
                    value={editFormData.first_name}
                    onChange={handleEditFormChange}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Last Name</label>
                  <input
                    type="text"
                    name="last_name"
                    value={editFormData.last_name}
                    onChange={handleEditFormChange}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={editFormData.email}
                    onChange={handleEditFormChange}
                    className="form-input"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Role *</label>
                  <select
                    name="role"
                    value={editFormData.role}
                    onChange={handleEditFormChange}
                    className="form-input"
                    required
                  >
                    <option value="STUDENT">Student</option>
                    <option value="FACULTY">Faculty</option>
                    <option value="ADMIN">Admin</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={editFormData.is_active}
                      onChange={handleEditFormChange}
                    />
                    <span>Account Active</span>
                  </label>
                  <small className="form-hint">
                    Inactive users cannot log in or access the system.
                  </small>
                </div>

                <div className="modal-actions">
                  <button 
                    type="button" 
                    className="btn-secondary"
                    onClick={closeEditModal}
                    disabled={editLoading}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="btn-primary"
                    disabled={editLoading}
                  >
                    {editLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUsers;
