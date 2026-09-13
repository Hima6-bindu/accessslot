/**
 * Admin Bookings Page
 * View and manage all bookings (Admin only)
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import BookingDetailsModal from '../components/BookingDetailsModal';
import '../styles/Pages.css';
import '../styles/Admin.css';

const AdminBookings = () => {
  const [bookings, setBookings] = useState([]);
  const [equipment, setEquipment] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [equipmentFilter, setEquipmentFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBooking, setSelectedBooking] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [bookingsRes, equipmentRes] = await Promise.all([
        api.get('/bookings/'),
        api.get('/equipment/')
      ]);
      
      setBookings(bookingsRes.data.results || bookingsRes.data);
      setEquipment(equipmentRes.data.results || equipmentRes.data);
      setError('');
    } catch (err) {
      setError('Failed to load bookings.');
      console.error('Error fetching bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredBookings = bookings.filter(booking => {
    const matchesStatus = statusFilter === 'ALL' || booking.status === statusFilter;
    const matchesEquipment = equipmentFilter === 'ALL' || booking.equipment === parseInt(equipmentFilter);
    const matchesSearch = !searchTerm || 
      booking.user_username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      booking.equipment_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesStatus && matchesEquipment && matchesSearch;
  });

  const handleViewBooking = async (bookingId) => {
    try {
      const response = await api.get(`/bookings/${bookingId}/`);
      setSelectedBooking(response.data);
    } catch (err) {
      console.error('Failed to fetch booking details:', err);
      setError('Failed to load booking details.');
    }
  };

  const handleBookingUpdate = (updatedBooking) => {
    setBookings(prev => 
      prev.map(booking => 
        booking.id === updatedBooking.id ? updatedBooking : booking
      )
    );
  };

  const getStatusCounts = () => {
    return {
      ALL: bookings.length,
      CONFIRMED: bookings.filter(b => b.status === 'CONFIRMED').length,
      CANCELLED: bookings.filter(b => b.status === 'CANCELLED').length,
      COMPLETED: bookings.filter(b => b.status === 'COMPLETED').length,
      NO_SHOW: bookings.filter(b => b.status === 'NO_SHOW').length,
    };
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading bookings...</div>
      </div>
    );
  }

  if (error && bookings.length === 0) {
    return (
      <div className="page-container">
        <div className="error-state">
          {error}
          <button className="btn-secondary" onClick={fetchData} style={{ marginTop: '15px' }}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const statusCounts = getStatusCounts();

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>All Bookings</h1>
          <p>View and manage all equipment bookings</p>
        </div>
        <button className="btn-secondary" onClick={fetchData}>
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="equipment-filters">
        <div className="filter-group">
          <input
            type="text"
            placeholder="Search by user or equipment..."
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
            <option value="ALL">All Status ({statusCounts.ALL})</option>
            <option value="CONFIRMED">Confirmed ({statusCounts.CONFIRMED})</option>
            <option value="CANCELLED">Cancelled ({statusCounts.CANCELLED})</option>
            <option value="COMPLETED">Completed ({statusCounts.COMPLETED})</option>
            <option value="NO_SHOW">No-show ({statusCounts.NO_SHOW})</option>
          </select>
        </div>

        <div className="filter-group">
          <select
            value={equipmentFilter}
            onChange={(e) => setEquipmentFilter(e.target.value)}
            className="filter-select"
          >
            <option value="ALL">All Equipment</option>
            {equipment.map(eq => (
              <option key={eq.id} value={eq.id}>{eq.name}</option>
            ))}
          </select>
        </div>
      </div>

      {filteredBookings.length === 0 ? (
        <div className="empty-state">
          <p>No bookings found matching your criteria.</p>
          {(searchTerm || statusFilter !== 'ALL' || equipmentFilter !== 'ALL') && (
            <button 
              className="btn-secondary"
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('ALL');
                setEquipmentFilter('ALL');
              }}
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="results-summary">
            Showing {filteredBookings.length} of {bookings.length} bookings
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User</th>
                  <th>Equipment</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredBookings.map((booking) => (
                  <tr key={booking.id}>
                    <td>#{booking.id}</td>
                    <td>
                      <div className="user-cell">
                        <strong>{booking.user_username}</strong>
                        <span className="user-role-mini">{booking.user_role || 'User'}</span>
                      </div>
                    </td>
                    <td>
                      <strong>{booking.equipment_name}</strong>
                      <div className="item-description">{booking.equipment_type}</div>
                    </td>
                    <td>
                      <div className="booking-time-cell">
                        {new Date(booking.start_time).toLocaleString()}
                      </div>
                    </td>
                    <td>
                      <div className="booking-time-cell">
                        {new Date(booking.end_time).toLocaleString()}
                      </div>
                    </td>
                    <td>{booking.duration_hours}h</td>
                    <td>
                      <span className={`status-badge status-${booking.status.toLowerCase()}`}>
                        {booking.status}
                      </span>
                    </td>
                    <td>
                      <button 
                        className="btn-small"
                        onClick={() => handleViewBooking(booking.id)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Booking Details Modal */}
      <BookingDetailsModal
        isOpen={!!selectedBooking}
        onClose={() => setSelectedBooking(null)}
        booking={selectedBooking}
        onBookingUpdate={handleBookingUpdate}
      />
    </div>
  );
};

export default AdminBookings;
