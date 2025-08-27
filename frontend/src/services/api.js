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

// Fine-Tuning API
export const fineTuningAPI = {
  // Models management
  getFineTunedModels: async (specialization = null) => {
    const params = specialization ? `?specialization=${specialization}` : '';
    const response = await apiClient.get(`/fine-tuned-models${params}`);
    return response.data;
  },

  createFineTunedModel: async (modelData) => {
    const response = await apiClient.post('/fine-tuned-models', modelData);
    return response.data;
  },

  getFineTunedModel: async (modelId) => {
    const response = await apiClient.get(`/fine-tuned-models/${modelId}`);
    return response.data;
  },

  updateFineTunedModel: async (modelId, updateData) => {
    const response = await apiClient.put(`/fine-tuned-models/${modelId}`, updateData);
    return response.data;
  },

  deleteFineTunedModel: async (modelId) => {
    const response = await apiClient.delete(`/fine-tuned-models/${modelId}`);
    return response.data;
  },

  // Dataset management
  uploadDataset: async (modelId, file, datasetType = 'jsonl', description = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataset_type', datasetType);
    formData.append('description', description);

    const response = await apiClient.post(`/fine-tuned-models/${modelId}/datasets`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getModelDatasets: async (modelId) => {
    const response = await apiClient.get(`/fine-tuned-models/${modelId}/datasets`);
    return response.data;
  },

  validateDataset: async (datasetId) => {
    const response = await apiClient.post(`/datasets/${datasetId}/validate`);
    return response.data;
  },

  // Training management
  startTraining: async (modelId, trainingParams = {}) => {
    const response = await apiClient.post(`/fine-tuned-models/${modelId}/start-training`, trainingParams);
    return response.data;
  },

  stopTraining: async (modelId) => {
    const response = await apiClient.post(`/fine-tuned-models/${modelId}/stop-training`);
    return response.data;
  },

  getTrainingStatus: async (modelId) => {
    const response = await apiClient.get(`/fine-tuned-models/${modelId}/status`);
    return response.data;
  },

  getTrainingLogs: async (modelId, limit = 50, logLevel = null) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (logLevel) params.append('log_level', logLevel);
    
    const response = await apiClient.get(`/fine-tuned-models/${modelId}/logs?${params}`);
    return response.data;
  },

  // Base models
  getBaseModels: async () => {
    const response = await apiClient.get('/base-models');
    return response.data;
  },

  // Admin endpoints
  getFineTuningOverview: async () => {
    const response = await apiClient.get('/admin/fine-tuning/overview');
    return response.data;
  },

  getActiveTrainings: async () => {
    const response = await apiClient.get('/admin/fine-tuning/active-trainings');
    return response.data;
  },

  getSystemStats: async () => {
    const response = await apiClient.get('/admin/fine-tuning/system-stats');
    return response.data;
  },
};

// Enhanced Query API with fine-tuned model support
export const enhancedQueryAPI = {
  ...queryAPI,
  
  createQueryWithModel: async (queryData, fineTunedModelId = null) => {
    const params = fineTunedModelId ? `?fine_tuned_model_id=${fineTunedModelId}` : '';
    const response = await apiClient.post(`/query${params}`, queryData);
    return response.data;
  },
};

export default apiClient;