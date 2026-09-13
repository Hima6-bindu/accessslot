/**
 * Main Application Layout
 * Contains sidebar, header, and main content area
 */
import { useState } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Layout.css';

const AppLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Navigation items based on role
  const getNavigationItems = () => {
    if (user?.role === 'ADMIN') {
      return [
        { path: '/admin-dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/equipment-admin', label: 'Equipment', icon: '🔧' },
        { path: '/bookings', label: 'Bookings', icon: '📅' },
        { path: '/maintenance', label: 'Maintenance', icon: '🔨' },
        { path: '/waiting-list', label: 'Waiting List', icon: '⏳' },
        { path: '/users', label: 'Users', icon: '👥' },
      ];
    } else {
      return [
        { path: '/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/equipment', label: 'Equipment', icon: '🔧' },
        { path: '/my-bookings', label: 'My Bookings', icon: '📅' },
        { path: '/my-waiting-list', label: 'My Waiting List', icon: '⏳' },
      ];
    }
  };

  const navigationItems = getNavigationItems();

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>AccessSlot</h2>
        </div>

        <nav className="sidebar-nav">
          {navigationItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className="nav-item"
            >
              <span className="nav-icon">{item.icon}</span>
              {sidebarOpen && <span className="nav-label">{item.label}</span>}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            {sidebarOpen && (
              <>
                <div className="user-name">{user?.username}</div>
                <div className="user-role">{user?.role}</div>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-wrapper">
        {/* Header */}
        <header className="app-header">
          <button className="sidebar-toggle" onClick={toggleSidebar}>
            {sidebarOpen ? '◀' : '▶'}
          </button>

          <div className="header-right">
            <div className="user-menu">
              <span className="user-name">{user?.first_name} {user?.last_name}</span>
              <span className="user-role-badge">{user?.role}</span>
              <button className="btn-logout" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
