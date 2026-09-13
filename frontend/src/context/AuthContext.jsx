/**
 * Authentication Context
 * Manages authentication state across the application
 */
import { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const currentUser = authService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    const { user } = await authService.login(username, password);
    setUser(user);
    return user;
  };

  const register = async (userData) => {
    const result = await authService.register(userData);
    return result;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const refreshProfile = async () => {
    try {
      const updatedUser = await authService.getProfile();
      setUser(updatedUser);
      return updatedUser;
    } catch (error) {
      console.error('Failed to refresh profile:', error);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    refreshProfile,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'ADMIN',
    isFaculty: user?.role === 'FACULTY',
    isStudent: user?.role === 'STUDENT',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
