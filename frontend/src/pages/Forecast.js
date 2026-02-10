import React, { useState } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import { forecastService } from '../services/api';

function Forecast() {
  const [formData, setFormData] = useState({
    data: '',
    model: 'auto',
    horizon: 7,
    confidence_level: 0.95,
    use_claude: false,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Parse data
      const dataArray = formData.data
        .split(',')
        .map(v => parseFloat(v.trim()))
        .filter(v => !isNaN(v));

      if (dataArray.length < 10) {
        throw new Error('Please provide at least 10 data points');
      }

      const requestData = {
        data: dataArray,
        model: formData.model,
        horizon: parseInt(formData.horizon),
        confidence_level: parseFloat(formData.confidence_level),
        use_claude: formData.use_claude,
      };

      const response = await forecastService.createForecast(requestData);
      setResult(response);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  const chartData = result ? result.predictions.map((value, index) => ({
    period: `T+${index + 1}`,
    prediction: parseFloat(value.toFixed(2)),
    lower: result.confidence_intervals?.lower?.[index] ? parseFloat(result.confidence_intervals.lower[index].toFixed(2)) : null,
    upper: result.confidence_intervals?.upper?.[index] ? parseFloat(result.confidence_intervals.upper[index].toFixed(2)) : null,
  })) : [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Demand Forecasting</h2>
          <p className="text-gray-600 mt-1">Generate forecasts using ensemble ML models</p>
        </div>
      </div>

      {/* Forecast Form */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Forecast Configuration</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Historical Data */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Historical Sales Data (comma-separated)
            </label>
            <textarea
              className="input-field"
              rows="3"
              placeholder="15234, 12450, 18500, 22100, 9800, 14200, 16750, 11500, 19800, 21500"
              value={formData.data}
              onChange={(e) => setFormData({ ...formData, data: e.target.value })}
              required
            />
            <p className="text-xs text-gray-500 mt-1">Minimum 10 data points required</p>
          </div>

          {/* Model Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Model</label>
              <select
                className="input-field"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              >
                <option value="auto">Auto (Best Model)</option>
                <option value="lstm">LSTM</option>
                <option value="arima">ARIMA</option>
                <option value="xgboost">XGBoost</option>
                <option value="lightgbm">LightGBM</option>
                <option value="prophet">Prophet</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Forecast Horizon</label>
              <input
                type="number"
                className="input-field"
                min="1"
                max="30"
                value={formData.horizon}
                onChange={(e) => setFormData({ ...formData, horizon: e.target.value })}
              />
            </div>
          </div>

          {/* Advanced Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Confidence Level</label>
              <select
                className="input-field"
                value={formData.confidence_level}
                onChange={(e) => setFormData({ ...formData, confidence_level: e.target.value })}
              >
                <option value="0.90">90%</option>
                <option value="0.95">95%</option>
                <option value="0.99">99%</option>
              </select>
            </div>

            <div className="flex items-center pt-8">
              <input
                type="checkbox"
                id="use_claude"
                checked={formData.use_claude}
                onChange={(e) => setFormData({ ...formData, use_claude: e.target.checked })}
                className="h-4 w-4 text-blue-600 rounded"
              />
              <label htmlFor="use_claude" className="ml-2 text-sm text-gray-700">
                Use Claude for AI explanation
              </label>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <RefreshCw className="animate-spin" size={20} />
                <span>Generating Forecast...</span>
              </>
            ) : (
              <>
                <TrendingUp size={20} />
                <span>Generate Forecast</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h4 className="text-red-800 font-medium">Error</h4>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <h4 className="text-sm text-gray-600 mb-1">Model Used</h4>
              <p className="text-2xl font-bold text-gray-900 uppercase">{result.model_used}</p>
            </div>
            <div className="card">
              <h4 className="text-sm text-gray-600 mb-1">MAPE</h4>
              <p className="text-2xl font-bold text-gray-900">{result.metrics?.mape?.toFixed(2)}%</p>
            </div>
            <div className="card">
              <h4 className="text-sm text-gray-600 mb-1">RMSE</h4>
              <p className="text-2xl font-bold text-gray-900">{result.metrics?.rmse?.toFixed(2)}</p>
            </div>
          </div>

          {/* Forecast Chart */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Forecast Visualization</h3>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="upper" stroke="#93c5fd" fill="#dbeafe" name="Upper Bound" />
                <Area type="monotone" dataKey="prediction" stroke="#3b82f6" fill="#60a5fa" name="Prediction" />
                <Area type="monotone" dataKey="lower" stroke="#93c5fd" fill="#dbeafe" name="Lower Bound" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Predictions Table */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Predicted Values</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Prediction</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lower Bound</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Upper Bound</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {chartData.map((row, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{row.period}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.prediction}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.lower || 'N/A'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.upper || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI Explanation */}
          {result.llm_explanation && (
            <div className="card bg-blue-50 border border-blue-200">
              <h3 className="text-lg font-semibold mb-2 text-blue-900">AI Insight</h3>
              <p className="text-blue-800">{result.llm_explanation}</p>
              <p className="text-xs text-blue-600 mt-2">Generated by {result.llm_used}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Forecast;
