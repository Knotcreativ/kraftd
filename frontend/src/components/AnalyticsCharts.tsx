/**
 * Analytics Charts Components
 * Recharts-based visualizations for historical event data
 */

import React, { useEffect, useState } from 'react';
import {
  LineChart,
  BarChart,
  AreaChart,
  ComposedChart,
  Line,
  Bar,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import './AnalyticsCharts.css';

interface ChartDataPoint {
  date: string;
  timestamp: number;
  value: number;
  count?: number;
  avg?: number;
  min?: number;
  max?: number;
  trend?: number;
  forecast?: number;
}

interface AnalyticsChartsProps {
  eventType: 'prices' | 'alerts' | 'anomalies' | 'signals' | 'trends';
  data?: ChartDataPoint[];
  isLoading?: boolean;
  period?: 'day' | 'week' | 'month';
}

interface PriceChartProps extends AnalyticsChartsProps {
  eventType: 'prices';
}

interface AlertChartProps extends AnalyticsChartsProps {
  eventType: 'alerts';
}

interface AnomalyChartProps extends AnalyticsChartsProps {
  eventType: 'anomalies';
}

interface SignalChartProps extends AnalyticsChartsProps {
  eventType: 'signals';
}

interface TrendChartProps extends AnalyticsChartsProps {
  eventType: 'trends';
}

/**
 * Price Chart - Shows price movements with trend line
 */
export const PriceChart: React.FC<PriceChartProps> = ({
  data = [],
  isLoading = false,
  period = 'day',
}) => {
  if (isLoading) {
    return <div className="chart-loading">Loading price data...</div>;
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        No price data available for the selected period
      </div>
    );
  }

  return (
    <div className="analytics-chart">
      <div className="chart-header">
        <h3>💰 Price Trends</h3>
        <span className="chart-period">{period}</span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            dataKey="date"
            stroke="#999"
            style={{ fontSize: '0.85rem' }}
          />
          <YAxis stroke="#999" style={{ fontSize: '0.85rem' }} />
          <Tooltip
            contentStyle={{
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #667eea',
              borderRadius: '8px',
              padding: '10px',
            }}
            formatter={(value: any) => `$${value.toFixed(2)}`}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="value"
            fill="#667eea"
            stroke="#667eea"
            fillOpacity={0.2}
            name="Price"
          />
          {data.some(d => d.trend) && (
            <Line
              type="monotone"
              dataKey="trend"
              stroke="#ff7300"
              strokeWidth={2}
              dot={false}
              name="Trend"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        {data.length > 0 && (
          <>
            <div className="stat">
              <span className="stat-label">Avg:</span>
              <span className="stat-value">
                ${(
                  data.reduce((sum, d) => sum + d.value, 0) / data.length
                ).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">High:</span>
              <span className="stat-value">
                ${Math.max(...data.map(d => d.value)).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Low:</span>
              <span className="stat-value">
                ${Math.min(...data.map(d => d.value)).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Change:</span>
              <span
                className={`stat-value ${
                  data[data.length - 1].value >= data[0].value
                    ? 'positive'
                    : 'negative'
                }`}
              >
                {(
                  data[data.length - 1].value - data[0].value
                ).toFixed(2)}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Alert Chart - Shows alert frequency over time
 */
export const AlertChart: React.FC<AlertChartProps> = ({
  data = [],
  isLoading = false,
  period = 'day',
}) => {
  if (isLoading) {
    return <div className="chart-loading">Loading alert data...</div>;
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        No alert data available for the selected period
      </div>
    );
  }

  return (
    <div className="analytics-chart">
      <div className="chart-header">
        <h3>⚠️ Alert Frequency</h3>
        <span className="chart-period">{period}</span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            dataKey="date"
            stroke="#999"
            style={{ fontSize: '0.85rem' }}
          />
          <YAxis stroke="#999" style={{ fontSize: '0.85rem' }} />
          <Tooltip
            contentStyle={{
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ff6b6b',
              borderRadius: '8px',
              padding: '10px',
            }}
          />
          <Legend />
          <Bar
            dataKey="count"
            fill="#ff6b6b"
            name="Alert Count"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        {data.length > 0 && (
          <>
            <div className="stat">
              <span className="stat-label">Total:</span>
              <span className="stat-value">
                {data.reduce((sum, d) => sum + (d.count || 0), 0)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Avg/Period:</span>
              <span className="stat-value">
                {(
                  data.reduce((sum, d) => sum + (d.count || 0), 0) /
                  data.length
                ).toFixed(1)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Peak:</span>
              <span className="stat-value">
                {Math.max(...data.map(d => d.count || 0))}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Trend:</span>
              <span
                className={`stat-value ${
                  data[data.length - 1].count ||
                  0 > (data[0].count || 0)
                    ? 'negative'
                    : 'positive'
                }`}
              >
                {data.length > 1
                  ? (data[data.length - 1].count ||
                      0) - (data[0].count || 0) > 0
                    ? 'Rising'
                    : 'Falling'
                  : '-'}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Anomaly Chart - Shows anomaly severity over time
 */
export const AnomalyChart: React.FC<AnomalyChartProps> = ({
  data = [],
  isLoading = false,
  period = 'day',
}) => {
  if (isLoading) {
    return <div className="chart-loading">Loading anomaly data...</div>;
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        No anomaly data available for the selected period
      </div>
    );
  }

  return (
    <div className="analytics-chart">
      <div className="chart-header">
        <h3>🔍 Anomaly Severity</h3>
        <span className="chart-period">{period}</span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            dataKey="date"
            stroke="#999"
            style={{ fontSize: '0.85rem' }}
          />
          <YAxis stroke="#999" style={{ fontSize: '0.85rem' }} />
          <Tooltip
            contentStyle={{
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #ffa726',
              borderRadius: '8px',
              padding: '10px',
            }}
            formatter={(value: any) => value.toFixed(2)}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="value"
            fill="#ffa726"
            stroke="#ffa726"
            fillOpacity={0.3}
            name="Z-Score"
          />
          {data.some(d => d.min) && (
            <Line
              type="monotone"
              dataKey="min"
              stroke="#81c784"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
              name="Min"
            />
          )}
          {data.some(d => d.max) && (
            <Line
              type="monotone"
              dataKey="max"
              stroke="#e53935"
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
              name="Max"
            />
          )}
        </AreaChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        {data.length > 0 && (
          <>
            <div className="stat">
              <span className="stat-label">Avg Score:</span>
              <span className="stat-value">
                {(
                  data.reduce((sum, d) => sum + d.value, 0) / data.length
                ).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Max Score:</span>
              <span className="stat-value">
                {Math.max(...data.map(d => d.value)).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Threshold:</span>
              <span className="stat-value">3.0 σ</span>
            </div>
            <div className="stat">
              <span className="stat-label">Critical:</span>
              <span className="stat-value negative">
                {data.filter(d => d.value > 3).length}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Signal Chart - Shows supplier signals over time
 */
export const SignalChart: React.FC<SignalChartProps> = ({
  data = [],
  isLoading = false,
  period = 'day',
}) => {
  if (isLoading) {
    return <div className="chart-loading">Loading signal data...</div>;
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        No signal data available for the selected period
      </div>
    );
  }

  return (
    <div className="analytics-chart">
      <div className="chart-header">
        <h3>🏭 Supplier Signals</h3>
        <span className="chart-period">{period}</span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            dataKey="date"
            stroke="#999"
            style={{ fontSize: '0.85rem' }}
          />
          <YAxis stroke="#999" style={{ fontSize: '0.85rem' }} />
          <Tooltip
            contentStyle={{
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #7c3aed',
              borderRadius: '8px',
              padding: '10px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#7c3aed"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Signal Value"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        {data.length > 0 && (
          <>
            <div className="stat">
              <span className="stat-label">Current:</span>
              <span className="stat-value">
                {data[data.length - 1].value.toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Change:</span>
              <span
                className={`stat-value ${
                  data[data.length - 1].value >= data[0].value
                    ? 'positive'
                    : 'negative'
                }`}
              >
                {(
                  data[data.length - 1].value - data[0].value
                ).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Volatility:</span>
              <span className="stat-value">
                {(
                  Math.max(...data.map(d => d.value)) -
                  Math.min(...data.map(d => d.value))
                ).toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Status:</span>
              <span
                className={`stat-value ${
                  data[data.length - 1].value > 0 ? 'positive' : 'negative'
                }`}
              >
                {data[data.length - 1].value > 0 ? 'Positive' : 'Negative'}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Trend Chart - Shows price trends with forecasts
 */
export const TrendChart: React.FC<TrendChartProps> = ({
  data = [],
  isLoading = false,
  period = 'day',
}) => {
  if (isLoading) {
    return <div className="chart-loading">Loading trend data...</div>;
  }

  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        No trend data available for the selected period
      </div>
    );
  }

  return (
    <div className="analytics-chart">
      <div className="chart-header">
        <h3>📈 Trend Analysis</h3>
        <span className="chart-period">{period}</span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            dataKey="date"
            stroke="#999"
            style={{ fontSize: '0.85rem' }}
          />
          <YAxis stroke="#999" style={{ fontSize: '0.85rem' }} />
          <Tooltip
            contentStyle={{
              background: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #10b981',
              borderRadius: '8px',
              padding: '10px',
            }}
            formatter={(value: any) => value.toFixed(2)}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="value"
            fill="#10b981"
            stroke="#10b981"
            fillOpacity={0.2}
            name="Actual"
          />
          {data.some(d => d.forecast) && (
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Forecast"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      <div className="chart-stats">
        {data.length > 0 && (
          <>
            <div className="stat">
              <span className="stat-label">Current:</span>
              <span className="stat-value">
                {data[data.length - 1].value.toFixed(2)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Forecast:</span>
              <span className="stat-value">
                {data.some(d => d.forecast)
                  ? data[data.length - 1].forecast?.toFixed(2) || '-'
                  : '-'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Confidence:</span>
              <span className="stat-value">85%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Direction:</span>
              <span
                className={`stat-value ${
                  data[data.length - 1].value >= data[0].value
                    ? 'positive'
                    : 'negative'
                }`}
              >
                {data[data.length - 1].value >= data[0].value
                  ? 'Uptrend'
                  : 'Downtrend'}
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default {
  PriceChart,
  AlertChart,
  AnomalyChart,
  SignalChart,
  TrendChart,
};
