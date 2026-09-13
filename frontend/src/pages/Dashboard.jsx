/**
 * Dashboard Page - Role-based routing
 */
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import '../styles/Pages.css';

const Dashboard = () => {
  const { user } = useAuth();

  // Admin users go to admin dashboard
  if (user?.role === 'ADMIN') {
    return <Navigate to="/admin-dashboard" replace />;
  }

  // Student/Faculty dashboard
  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Welcome back, {user?.first_name}!</p>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-icon">🔧</div>
          <div className="card-content">
            <h3>Equipment</h3>
            <p>Browse available equipment</p>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">📅</div>
          <div className="card-content">
            <h3>My Bookings</h3>
            <p>View and manage bookings</p>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-icon">⏳</div>
          <div className="card-content">
            <h3>Waiting List</h3>
            <p>Check your waiting list status</p>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h2>Quick Stats</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">-</div>
            <div className="stat-label">Active Bookings</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">-</div>
            <div className="stat-label">Available Equipment</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">-</div>
            <div className="stat-label">Weekly Hours</div>
          </div>
        </div>
        <p className="info-note">Statistics will be populated with real data in future updates.</p>
      </div>
    </div>
  );
};

export default Dashboard;
