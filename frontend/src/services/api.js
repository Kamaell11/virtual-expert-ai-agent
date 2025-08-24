import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('accessToken');
      localStorage.removeItem('userData');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (credentials) => {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  register: async (userData) => {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  setToken: (token) => {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  },
};

// Query API
export const queryAPI = {
  createQuery: async (queryData) => {
    const response = await apiClient.post('/query', queryData);
    return response.data;
  },

  getQueries: async (skip = 0, limit = 20) => {
    const response = await apiClient.get(`/queries?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  deleteQuery: async (queryId) => {
    const response = await apiClient.delete(`/queries/${queryId}`);
    return response.data;
  },
};

// Model API
export const modelAPI = {
  getAvailableModels: async () => {
    const response = await apiClient.get('/models');
    return response.data;
  },

  switchModel: async (modelName) => {
    const response = await apiClient.post(`/models/switch/${modelName}`);
    return response.data;
  },
};

// System API
export const systemAPI = {
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getSystemInfo: async () => {
    const response = await apiClient.get('/');
    return response.data;
  },
};

export default apiClient;