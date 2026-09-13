/**
 * Admin Dashboard Overview
 * Real-time statistics and summary for administrators
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import '../styles/Pages.css';
import '../styles/Admin.css';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalEquipment: 0,
    availableEquipment: 0,
    maintenanceEquipment: 0,
    upcomingBookings: 0,
    activeBookings: 0,
    waitingListEntries: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    setLoading(true);
    setError('');

    try {
      // Fetch data from multiple endpoints in parallel
      const [equipmentRes, bookingsRes, waitingListRes] = await Promise.all([
        api.get('/equipment/'),
        api.get('/bookings/'),
        api.get('/waiting-list/')
      ]);

      const equipment = equipmentRes.data.results || equipmentRes.data;
      const bookings = bookingsRes.data.results || bookingsRes.data;
      const waitingList = waitingListRes.data.results || waitingListRes.data;

      // Calculate statistics
      const now = new Date();
      const upcomingBookings = bookings.filter(b => 
        b.status === 'CONFIRMED' && new Date(b.start_time) > now
      ).length;

      const activeBookings = bookings.filter(b => {
        const start = new Date(b.start_time);
        const end = new Date(b.end_time);
        return b.status === 'CONFIRMED' && start <= now && now <= end;
      }).length;

      setStats({
        totalUsers: 0, // Note: No users list endpoint available in backend
        totalEquipment: equipment.length,
        availableEquipment: equipment.filter(e => e.status === 'AVAILABLE').length,
        maintenanceEquipment: equipment.filter(e => e.status === 'MAINTENANCE').length,
        upcomingBookings,
        activeBookings,
        waitingListEntries: waitingList.length,
      });
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err);
      setError('Failed to load dashboard statistics. Some features may be unavailable.');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { 
      label: 'Total Equipment', 
      value: stats.totalEquipment, 
      icon: '🔧', 
      color: '#667eea',
      link: '/equipment-admin'
    },
    { 
      label: 'Available Equipment', 
      value: stats.availableEquipment, 
      icon: '✅', 
      color: '#155724',
      link: '/equipment-admin'
    },
    { 
      label: 'Under Maintenance', 
      value: stats.maintenanceEquipment, 
      icon: '🔨', 
      color: '#856404',
      link: '/maintenance'
    },
    { 
      label: 'Active Bookings', 
      value: stats.activeBookings, 
      icon: '📅', 
      color: '#0c5460',
      link: '/bookings'
    },
    { 
      label: 'Upcoming Bookings', 
      value: stats.upcomingBookings, 
      icon: '📆', 
      color: '#004085',
      link: '/bookings'
    },
    { 
      label: 'Waiting List', 
      value: stats.waitingListEntries, 
      icon: '⏳', 
      color: '#721c24',
      link: '/waiting-list'
    },
  ];

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p>System overview and real-time statistics</p>
        </div>
        <button className="btn-secondary" onClick={fetchDashboardStats}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="info-message">
          {error}
        </div>
      )}

      <div className="admin-stats-grid">
        {statCards.map((card, index) => (
          <Link 
            key={index} 
            to={card.link} 
            className="stat-card-link"
          >
            <div className="stat-card-admin" style={{ borderColor: card.color }}>
              <div className="stat-icon" style={{ color: card.color }}>
                {card.icon}
              </div>
              <div className="stat-details">
                <div className="stat-value-admin" style={{ color: card.color }}>
                  {card.value}
                </div>
                <div className="stat-label-admin">{card.label}</div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="admin-quick-links">
        <h2>Quick Actions</h2>
        <div className="quick-links-grid">
          <Link to="/equipment-admin" className="quick-link-card">
            <span className="quick-link-icon">🔧</span>
            <span className="quick-link-text">Manage Equipment</span>
          </Link>
          <Link to="/bookings" className="quick-link-card">
            <span className="quick-link-icon">📅</span>
            <span className="quick-link-text">View All Bookings</span>
          </Link>
          <Link to="/maintenance" className="quick-link-card">
            <span className="quick-link-icon">🔨</span>
            <span className="quick-link-text">Schedule Maintenance</span>
          </Link>
          <Link to="/waiting-list" className="quick-link-card">
            <span className="quick-link-icon">⏳</span>
            <span className="quick-link-text">Manage Waiting List</span>
          </Link>
          <Link to="/users" className="quick-link-card">
            <span className="quick-link-icon">👥</span>
            <span className="quick-link-text">View Users</span>
          </Link>
        </div>
      </div>

      {stats.totalUsers === 0 && (
        <div className="admin-note">
          <strong>Note:</strong> User statistics are not available because the backend does not provide a users list endpoint. 
          User management is currently read-only or unavailable.
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;