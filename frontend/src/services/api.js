import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const forecastService = {
  // Demand Forecasting
  createForecast: async (data) => {
    const response = await api.post('/api/forecast/demand', data);
    return response.data;
  },

  // Lot Sizing
  calculateLotSizing: async (data) => {
    const response = await api.post('/api/forecast/lot-sizing', data);
    return response.data;
  },

  // Production Schedule
  optimizeProduction: async (data) => {
    const response = await api.post('/api/forecast/production-schedule', data);
    return response.data;
  },

  // Materials Acquisition
  planMaterials: async (data) => {
    const response = await api.post('/api/forecast/materials-acquisition', data);
    return response.data;
  },

  // Models Status
  getModelsStatus: async () => {
    const response = await api.get('/api/forecast/models/status');
    return response.data;
  },
};

export const dataService = {
  // Upload Data
  uploadData: async (file, autoTrain = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_train', autoTrain);
    
    const response = await api.post('/api/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // List Datasets
  getDatasets: async () => {
    const response = await api.get('/api/data/datasets');
    return response.data;
  },

  // Get Dataset by ID
  getDataset: async (id) => {
    const response = await api.get(`/api/data/datasets/${id}`);
    return response.data;
  },

  // Delete Dataset
  deleteDataset: async (id) => {
    const response = await api.delete(`/api/data/datasets/${id}`);
    return response.data;
  },

  // Get Statistics
  getStatistics: async () => {
    const response = await api.get('/api/data/statistics');
    return response.data;
  },

  // Training Status
  getTrainingStatus: async (jobId) => {
    const response = await api.get(`/api/data/train/status/${jobId}`);
    return response.data;
  },
};

export const ragService = {
  // Query Knowledge Base
  query: async (question, useClaude = false) => {
    const response = await api.post('/api/rag/query', {
      question,
      use_claude: useClaude,
      top_k: 5,
    });
    return response.data;
  },

  // Get KB Stats
  getKBStats: async () => {
    const response = await api.get('/api/rag/knowledge-base/stats');
    return response.data;
  },
};

export const healthService = {
  // Health Check
  getHealth: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },
};

export default api;
