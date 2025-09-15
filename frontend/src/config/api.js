/**
 * API Configuration
 * Centralized API endpoint and environment configuration
 */

// Environment-based API configuration
const getAPIBaseURL = () => {
  // Check for environment variable first (for production)
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Development environment detection
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:5000';
  }
  
  // Production fallback (adjust as needed)
  return 'https://your-api-domain.com';
};

export const API_BASE_URL = getAPIBaseURL();

// API endpoint constants
export const API_ENDPOINTS = {
  // Health & System
  HEALTH: '/api/health',
  
  // User endpoints
  USER_PROFILE: '/api/user/profile',
  USER_HISTORY: '/api/user/history',
  
  // AOI endpoints
  AOI_LIST: '/api/aoi',
  AOI_CREATE: '/api/aoi',
  AOI_DELETE: (id) => `/api/aoi/${id}`,
  AOI_GET: (id) => `/api/aoi/${id}`,
  AOI_DASHBOARD: (id) => `/api/aoi/${id}/dashboard`,
  AOI_HISTORY: (id) => `/api/aoi/${id}/history`,
  AOI_SCHEDULE: (id) => `/api/aoi/${id}/schedule-monitoring`,
  AOI_BASELINE: (id) => `/api/aoi/${id}/baseline`,
  
  // Analysis endpoints
  PROCESS_IMAGES: '/api/process-satellite-images',
  RUN_ANALYSIS: (id) => `/api/aoi/${id}/run-analysis`,
  
  // Admin endpoints
  ADMIN_STATS: '/api/admin/stats',
  
  // Images
  IMAGE: (filename) => `/api/image/${filename}`
};

// Development helper
export const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';

// API utilities
export const buildImageURL = (filename) => {
  return `${API_BASE_URL}${API_ENDPOINTS.IMAGE(filename)}`;
};

export const buildFullURL = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`;
};