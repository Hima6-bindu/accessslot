/**
 * Authentication service for user login, registration, and session management
 */
import api from './api';

const authService = {
  /**
   * Login user
   */
  async login(username, password) {
    const response = await api.post('/auth/login/', {
      username,
      password,
    });

    const { access, refresh, user } = response.data;

    // Store tokens and user info
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
    localStorage.setItem('user', JSON.stringify(user));

    return { access, refresh, user };
  },

  /**
   * Register new user
   */
  async register(userData) {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  /**
   * Logout user
   */
  logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
  },

  /**
   * Get current user from localStorage
   */
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('accessToken');
  },

  /**
   * Get user profile from backend
   */
  async getProfile() {
    const response = await api.get('/auth/profile/');
    const user = response.data;
    localStorage.setItem('user', JSON.stringify(user));
    return user;
  },

  /**
   * Refresh access token
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });

    const { access } = response.data;
    localStorage.setItem('accessToken', access);
    return access;
  },
};

export default authService;
