import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Activity, Database, Cpu } from 'lucide-react';
import { dataService, healthService } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsData, healthData, datasetsData] = await Promise.all([
        dataService.getStatistics(),
        healthService.getHealth(),
        dataService.getDatasets(),
      ]);
      setStats(statsData);
      setHealth(healthData);
      setDatasets(datasetsData.datasets || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
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
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-8 text-white">
        <h2 className="text-3xl font-bold mb-2">Welcome to ChronoForge Pulse</h2>
        <p className="text-blue-100">AI-powered time series forecasting with ensemble ML models</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Database className="text-blue-600" size={24} />}
          title="Total Datasets"
          value={stats?.total_datasets || 0}
          color="blue"
        />
        <StatCard
          icon={<Activity className="text-green-600" size={24} />}
          title="Total Records"
          value={stats?.total_records || 0}
          color="green"
        />
        <StatCard
          icon={<Cpu className="text-purple-600" size={24} />}
          title="ML Models"
          value={health?.models ? Object.keys(health.models).length : 0}
          color="purple"
        />
        <StatCard
          icon={<TrendingUp className="text-orange-600" size={24} />}
          title="API Status"
          value={health?.status === 'healthy' ? 'Healthy' : 'Offline'}
          color="orange"
        />
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Services Status */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Services Status</h3>
          <div className="space-y-3">
            {health?.services && Object.entries(health.services).map(([service, status]) => (
              <div key={service} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium capitalize">{service.replace('_', ' ')}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  status === 'operational' || status === 'available' || status === 'configured'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Models Status */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">ML Models Status</h3>
          <div className="space-y-3">
            {health?.models && Object.entries(health.models).map(([model, status]) => (
              <div key={model} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium uppercase">{model}</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  status === 'available'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Datasets */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Recent Datasets</h3>
        {datasets.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Records</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uploaded</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {datasets.slice(0, 5).map((dataset) => (
                  <tr key={dataset.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{dataset.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{dataset.record_count}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(dataset.uploaded_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No datasets uploaded yet. Upload data to get started.</p>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, title, value, color }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 bg-${color}-50 rounded-lg`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
