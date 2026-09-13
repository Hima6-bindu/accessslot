/**
 * Application Routes Configuration
 */
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import AppLayout from '../layouts/AppLayout';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Dashboard from '../pages/Dashboard';
import Equipment from '../pages/Equipment';
import MyBookings from '../pages/MyBookings';
import MyWaitingList from '../pages/MyWaitingList';
import Maintenance from '../pages/Maintenance';
import AdminBookings from '../pages/AdminBookings';
import AdminUsers from '../pages/AdminUsers';
import AdminDashboard from '../pages/AdminDashboard';
import EquipmentAdmin from '../pages/EquipmentAdmin';

const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {/* Common Routes */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />

        {/* Student/Faculty Routes */}
        <Route
          path="equipment"
          element={
            <ProtectedRoute allowedRoles={['STUDENT', 'FACULTY']}>
              <Equipment />
            </ProtectedRoute>
          }
        />
        <Route
          path="my-bookings"
          element={
            <ProtectedRoute allowedRoles={['STUDENT', 'FACULTY']}>
              <MyBookings />
            </ProtectedRoute>
          }
        />
        <Route
          path="my-waiting-list"
          element={
            <ProtectedRoute allowedRoles={['STUDENT', 'FACULTY']}>
              <MyWaitingList />
            </ProtectedRoute>
          }
        />

        {/* Admin Only Routes */}
        <Route
          path="admin-dashboard"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="equipment-admin"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <EquipmentAdmin />
            </ProtectedRoute>
          }
        />
        <Route
          path="bookings"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminBookings />
            </ProtectedRoute>
          }
        />
        <Route
          path="maintenance"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <Maintenance />
            </ProtectedRoute>
          }
        />
        <Route
          path="waiting-list"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <MyWaitingList />
            </ProtectedRoute>
          }
        />
        <Route
          path="users"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminUsers />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch all - redirect to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default AppRoutes;
