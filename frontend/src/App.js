import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, BarChart3, Upload, Settings, TrendingUp } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Forecast from './pages/Forecast';
import DataUpload from './pages/DataUpload';
import SettingsPage from './pages/SettingsPage';
import { healthService } from './services/api';

function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const data = await healthService.getHealth();
      setHealth(data);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
                  <TrendingUp className="text-white" size={28} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">ChronoForge Pulse</h1>
                  <p className="text-sm text-gray-500">Time Series Forecasting Platform</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {health && (
                  <div className="flex items-center space-x-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-gray-600">{health.status === 'healthy' ? 'Online' : 'Offline'}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/upload" element={<DataUpload />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-gray-500">
              © 2026 ChronoForge Pulse. Powered by AI-driven forecasting.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

function Navigation() {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  const navItems = [
    { path: '/', icon: Activity, label: 'Dashboard' },
    { path: '/forecast', icon: BarChart3, label: 'Forecast' },
    { path: '/upload', icon: Upload, label: 'Data Upload' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          {navItems.map(({ path, icon: Icon, label }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center space-x-2 py-4 px-2 border-b-2 transition-colors ${
                isActive(path)
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default App;
