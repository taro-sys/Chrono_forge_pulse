import React, { useState, useEffect } from 'react';
import { Settings, Database, Cpu, Activity } from 'lucide-react';
import { healthService, forecastService } from '../services/api';

function SettingsPage() {
  const [health, setHealth] = useState(null);
  const [modelsStatus, setModelsStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const [healthData, modelsData] = await Promise.all([
        healthService.getHealth(),
        forecastService.getModelsStatus(),
      ]);
      setHealth(healthData);
      setModelsStatus(modelsData);
    } catch (error) {
      console.error('Failed to load system info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Settings & System Status</h2>
        <p className="text-gray-600 mt-1">View system configuration and service status</p>
      </div>

      {/* System Health */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-4">
          <Activity className="text-blue-600" size={24} />
          <h3 className="text-lg font-semibold">System Health</h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <span className="font-medium">Overall Status</span>
            <span className={`px-4 py-2 rounded-full font-medium ${
              health?.status === 'healthy'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {health?.status || 'Unknown'}
            </span>
          </div>
        </div>
      </div>

      {/* Services Status */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-4">
          <Database className="text-blue-600" size={24} />
          <h3 className="text-lg font-semibold">Services</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {health?.services && Object.entries(health.services).map(([service, status]) => (
            <div key={service} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="font-medium capitalize">{service.replace('_', ' ')}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  status === 'operational' || status === 'available' || status === 'configured'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ML Models */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-4">
          <Cpu className="text-blue-600" size={24} />
          <h3 className="text-lg font-semibold">ML Models</h3>
        </div>
        <div className="space-y-4">
          {/* Model Availability */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Available Models</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {health?.models && Object.entries(health.models).map(([model, status]) => (
                <div key={model} className="p-3 bg-gray-50 rounded-lg flex items-center justify-between">
                  <span className="font-medium uppercase text-sm">{model}</span>
                  <span className={`w-2 h-2 rounded-full ${
                    status === 'available' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}></span>
                </div>
              ))}
            </div>
          </div>

          {/* Model Settings */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Configuration</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Auto Selection</span>
                <span className="font-medium">{modelsStatus?.auto_selection_enabled ? 'Enabled' : 'Disabled'}</span>
              </div>
              <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Pretrained Models Loaded</span>
                <span className="font-medium">{modelsStatus?.pretrained_loaded ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Information */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-4">
          <Settings className="text-blue-600" size={24} />
          <h3 className="text-lg font-semibold">API Configuration</h3>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-600">Backend URL</span>
            <span className="font-medium">{process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'}</span>
          </div>
          <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-600">API Version</span>
            <span className="font-medium">v1.0</span>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="card bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200">
        <h3 className="text-lg font-semibold mb-2">About ChronoForge Pulse</h3>
        <p className="text-gray-700 text-sm">
          ChronoForge Pulse is an AI-powered time series forecasting platform featuring:
        </p>
        <ul className="mt-2 space-y-1 text-sm text-gray-600">
          <li>• Ensemble ML Models (LSTM, ARIMA, XGBoost, LightGBM, Prophet)</li>
          <li>• Automatic Model Selection based on MAPE/RMSE</li>
          <li>• Dual LLM Integration (Ollama + Claude)</li>
          <li>• Real-time Forecasting & Analysis</li>
          <li>• Background Model Training</li>
        </ul>
        <p className="mt-3 text-xs text-gray-500">
          © 2026 ChronoForge Pulse. All rights reserved.
        </p>
      </div>
    </div>
  );
}

export default SettingsPage;
