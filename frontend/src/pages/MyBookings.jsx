/**
 * My Bookings Page
 * Enhanced booking management with filters and actions
 */
import { useState, useEffect } from 'react';
import api from '../services/api';
import BookingDetailsModal from '../components/BookingDetailsModal';
import '../styles/Pages.css';

const MyBookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/bookings/');
      setBookings(response.data.results || response.data);
      setError('');
    } catch (err) {
      setError('Failed to load bookings.');
      console.error('Error fetching bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredBookings = bookings.filter(booking => {
    if (statusFilter === 'ALL') return true;
    return booking.status === statusFilter;
  });

  const handleBookingUpdate = (updatedBooking) => {
    setBookings(prev => 
      prev.map(booking => 
        booking.id === updatedBooking.id ? updatedBooking : booking
      )
    );
    
    if (updatedBooking.status === 'CANCELLED') {
      setMessage('Booking cancelled successfully.');
      setTimeout(() => setMessage(''), 5000);
    }
  };

  const handleViewBooking = async (bookingId) => {
    try {
      const response = await api.get(`/bookings/${bookingId}/`);
      setSelectedBooking(response.data);
    } catch (err) {
      console.error('Failed to fetch booking details:', err);
      setError('Failed to load booking details.');
    }
  };

  const getStatusCounts = () => {
    const counts = {
      ALL: bookings.length,
      CONFIRMED: bookings.filter(b => b.status === 'CONFIRMED').length,
      CANCELLED: bookings.filter(b => b.status === 'CANCELLED').length,
      COMPLETED: bookings.filter(b => b.status === 'COMPLETED').length,
      NO_SHOW: bookings.filter(b => b.status === 'NO_SHOW').length,
    };
    return counts;
  };

  const isBookingActive = (booking) => {
    const now = new Date();
    const start = new Date(booking.start_time);
    const end = new Date(booking.end_time);
    return booking.status === 'CONFIRMED' && start <= now && now <= end;
  };

  const isBookingUpcoming = (booking) => {
    const now = new Date();
    const start = new Date(booking.start_time);
    return booking.status === 'CONFIRMED' && start > now;
  };

  const canCancelBooking = (booking) => {
    return booking.status === 'CONFIRMED' && new Date(booking.start_time) > new Date();
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading bookings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-state">
          {error}
          <button className="btn-secondary" onClick={fetchBookings} style={{ marginTop: '15px' }}>
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
          <h1>My Bookings</h1>
          <p>View and manage your equipment bookings</p>
        </div>
        <button className="btn-secondary" onClick={fetchBookings}>
          Refresh
        </button>
      </div>

      {message && (
        <div className="success-message">
          {message}
          <button className="close-message" onClick={() => setMessage('')}>×</button>
        </div>
      )}

      {/* Status Filter Tabs */}
      <div className="booking-filters">
        <label>Filter by status:</label>
        {Object.entries(statusCounts).map(([status, count]) => (
          <button
            key={status}
            className={`filter-tab ${statusFilter === status ? 'active' : ''}`}
            onClick={() => setStatusFilter(status)}
          >
            {status === 'ALL' ? 'All' : status} ({count})
          </button>
        ))}
      </div>

      {filteredBookings.length === 0 ? (
        <div className="empty-state">
          {statusFilter === 'ALL' ? (
            <div>
              <p>You don't have any bookings yet.</p>
              <p>Visit the Equipment page to make a booking.</p>
            </div>
          ) : (
            <div>
              <p>No {statusFilter.toLowerCase()} bookings found.</p>
              <button 
                className="btn-secondary"
                onClick={() => setStatusFilter('ALL')}
              >
                View All Bookings
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Equipment</th>
                <th>Start Time</th>
                <th>End Time</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredBookings.map((booking) => {
                const isActive = isBookingActive(booking);
                const isUpcoming = isBookingUpcoming(booking);
                
                return (
                  <tr key={booking.id} className={isActive ? 'active-booking' : ''}>
                    <td>#{booking.id}</td>
                    <td>
                      <div>
                        <strong>{booking.equipment_name}</strong>
                        {isActive && <span className="live-badge">LIVE</span>}
                        {isUpcoming && <span className="upcoming-badge">UPCOMING</span>}
                      </div>
                    </td>
                    <td>{new Date(booking.start_time).toLocaleString()}</td>
                    <td>{new Date(booking.end_time).toLocaleString()}</td>
                    <td>{booking.duration_hours}h</td>
                    <td>
                      <span className={`status-badge status-${booking.status.toLowerCase()}`}>
                        {booking.status}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button 
                          className="btn-small"
                          onClick={() => handleViewBooking(booking.id)}
                        >
                          View
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

export default MyBookings;
