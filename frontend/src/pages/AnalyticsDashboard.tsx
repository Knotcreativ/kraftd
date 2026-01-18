/**
 * Analytics Dashboard Page
 * Displays historical data with charts, filters, KPI cards, and data export
 * Phase 10: Connected to real API endpoints
 */

import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import FilterPanel from '../components/FilterPanel';
import {
  PriceChart,
  AlertChart,
  AnomalyChart,
  SignalChart,
  TrendChart,
} from '../components/AnalyticsCharts';
import {
  exportAsCSV,
  exportAsExcel,
  exportAsJSON,
  generateChartExportData,
  ExportData,
} from '../services/exportService';
import './AnalyticsDashboard.css';

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

interface KPICard {
  title: string;
  value: string | number;
  change?: string;
  icon: string;
  color: string;
  trend?: 'up' | 'down' | 'stable';
}

interface FilterState {
  startDate: Date;
  endDate: Date;
  itemId?: string;
  supplierId?: string;
  severity?: string;
  riskLevel?: string;
  displayMode: 'compact' | 'expanded';
}

export const AnalyticsDashboard: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    startDate: new Date(new Date().setDate(new Date().getDate() - 30)),
    endDate: new Date(),
    displayMode: 'compact',
  });
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // State for chart data
  const [priceData, setPriceData] = useState<ChartDataPoint[]>([]);
  const [alertData, setAlertData] = useState<ChartDataPoint[]>([]);
  const [anomalyData, setAnomalyData] = useState<ChartDataPoint[]>([]);
  const [signalData, setSignalData] = useState<ChartDataPoint[]>([]);
  const [trendData, setTrendData] = useState<ChartDataPoint[]>([]);
  const [kpiCards, setKpiCards] = useState<KPICard[]>([
    {
      title: 'Total Alerts',
      value: 0,
      change: '--',
      icon: '⚠️',
      color: 'red',
      trend: 'stable',
    },
    {
      title: 'Avg Price',
      value: '$0.00',
      change: '--',
      icon: '💰',
      color: 'green',
      trend: 'stable',
    },
    {
      title: 'Anomalies',
      value: 0,
      change: '--',
      icon: '🔍',
      color: 'orange',
      trend: 'stable',
    },
    {
      title: 'Suppliers',
      value: 0,
      change: 'Stable',
      icon: '🏭',
      color: 'blue',
      trend: 'stable',
    },
  ]);

  const items = ['Wheat', 'Corn', 'Soybeans', 'Coffee', 'Cocoa'];
  const suppliers = ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D', 'Supplier E'];

  // Convert Date to YYYY-MM-DD format for API
  const formatDateForApi = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  // Transform API response to chart data format
  const transformEventData = (apiData: any): ChartDataPoint[] => {
    if (!apiData || !apiData.results) return [];
    
    return apiData.results.map((item: any, index: number) => ({
      date: new Date(item.timestamp || item.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      timestamp: new Date(item.timestamp || item.date).getTime(),
      value: item.value || item.price || item.score || 0,
      count: item.count || 1,
      avg: item.avg || item.value || 0,
      min: item.min || 0,
      max: item.max || item.value || 0,
      trend: item.trend || (item.value || 0),
      forecast: item.forecast || (item.value || 0),
    }));
  };

  // Fetch event data from API
  const fetchEventData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const startDate = formatDateForApi(filters.startDate);
      const endDate = formatDateForApi(filters.endDate);

      // Fetch all event types in parallel
      const [
        pricesResponse,
        alertsResponse,
        anomaliesResponse,
        signalsResponse,
        trendsResponse,
        statsResponse
      ] = await Promise.all([
        apiClient.getEventPrices(startDate, endDate),
        apiClient.getEventAlerts(startDate, endDate),
        apiClient.getEventAnomalies(startDate, endDate),
        apiClient.getEventSignals(startDate, endDate),
        apiClient.getEventTrends(startDate, endDate),
        apiClient.getEventStats(startDate, endDate)
      ]);

      // Transform data
      const prices = transformEventData(pricesResponse);
      const alerts = transformEventData(alertsResponse);
      const anomalies = transformEventData(anomaliesResponse);
      const signals = transformEventData(signalsResponse);
      const trends = transformEventData(trendsResponse);

      setPriceData(prices);
      setAlertData(alerts);
      setAnomalyData(anomalies);
      setSignalData(signals);
      setTrendData(trends);

      // Update KPI cards from stats
      if (statsResponse) {
        const avgPrice = prices.length > 0 
          ? (prices.reduce((sum: number, p: ChartDataPoint) => sum + (p.value || 0), 0) / prices.length).toFixed(2)
          : '0.00';

        const newKpiCards: KPICard[] = [
          {
            title: 'Total Alerts',
            value: statsResponse.alert || 0,
            change: `${alerts.length > 0 ? '+' : ''}${alerts.length}`,
            icon: '⚠️',
            color: 'red',
            trend: alerts.length > 0 ? 'up' : 'stable',
          },
          {
            title: 'Avg Price',
            value: `$${avgPrice}`,
            change: '+0%',
            icon: '💰',
            color: 'green',
            trend: 'stable',
          },
          {
            title: 'Anomalies',
            value: statsResponse.anomaly || 0,
            change: `${anomalies.length}`,
            icon: '🔍',
            color: 'orange',
            trend: anomalies.length > 5 ? 'up' : 'down',
          },
          {
            title: 'Suppliers',
            value: statsResponse.signal || 0,
            change: 'Stable',
            icon: '🏭',
            color: 'blue',
            trend: 'stable',
          },
        ];
        setKpiCards(newKpiCards);
      }
    } catch (err) {
      console.error('Failed to fetch event data:', err);
      setError('Failed to load analytics data. Please try again.');
      // Fallback: set empty arrays to prevent chart errors
      setPriceData([]);
      setAlertData([]);
      setAnomalyData([]);
      setSignalData([]);
      setTrendData([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount and when filters change
  useEffect(() => {
    fetchEventData();
  }, [filters]);

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  const handleExport = async (format: 'csv' | 'xlsx' | 'json') => {
    try {
      setExportMessage(null);
      
      // Prepare filter metadata
      const filterMetadata = {
        dateRange: `${filters.startDate.toLocaleDateString()} to ${filters.endDate.toLocaleDateString()}`,
        item: filters.itemId || 'All',
        supplier: filters.supplierId || 'All',
        period,
      };

      // Generate export data for all charts
      const chartTypes: Array<'price' | 'alert' | 'anomaly' | 'signal' | 'trend'> = [
        'price',
        'alert',
        'anomaly',
        'signal',
        'trend',
      ];

      chartTypes.forEach(chartType => {
        const exportData = generateChartExportData(chartType, filterMetadata);
        
        if (format === 'csv') {
          exportAsCSV(exportData);
        } else if (format === 'xlsx') {
          exportAsExcel(exportData);
        } else if (format === 'json') {
          exportAsJSON(exportData);
        }
      });

      const formatLabel = format === 'xlsx' ? 'Excel' : format.toUpperCase();
      setExportMessage({
        type: 'success',
        text: `Successfully exported ${chartTypes.length} charts as ${formatLabel}!`,
      });

      // Clear message after 4 seconds
      setTimeout(() => setExportMessage(null), 4000);
    } catch (error) {
      console.error('Export failed:', error);
      setExportMessage({
        type: 'error',
        text: 'Failed to export data. Please try again.',
      });
    }
  };

  return (
    <div className="analytics-dashboard-page">
      <header className="analytics-page-header">
        <div className="header-content">
          <h1>📊 Historical Analytics</h1>
          <p>Analyze trends, patterns, and insights from your data</p>
        </div>
      </header>

      {/* Error Message */}
      {error && (
        <div className="error-alert">
          <span className="alert-close" onClick={() => setError(null)}>✕</span>
          <strong>Error:</strong> {error}
          <button className="btn-retry" onClick={fetchEventData}>Retry</button>
        </div>
      )}

      {/* Filter Panel */}
      <FilterPanel
        onFilterChange={handleFilterChange}
        items={items}
        suppliers={suppliers}
      />

      {/* Period Selector */}
      <div className="period-selector">
        <label>Aggregation Period:</label>
        <div className="period-buttons">
          {['day', 'week', 'month'].map(p => (
            <button
              key={p}
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p as 'day' | 'week' | 'month')}
            >
              {p === 'day'
                ? 'Daily'
                : p === 'week'
                ? 'Weekly'
                : 'Monthly'}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <section className="kpi-section">
        <h2>Key Metrics</h2>
        <div className="kpi-grid">
          {kpiCards.map((card, idx) => (
            <div key={idx} className={`kpi-card kpi-card--${card.color}`}>
              <div className="kpi-icon">{card.icon}</div>
              <div className="kpi-content">
                <h3 className="kpi-title">{card.title}</h3>
                <p className="kpi-value">{isLoading ? '...' : card.value}</p>
                {card.change && (
                  <p
                    className={`kpi-change kpi-change--${
                      card.trend === 'up'
                        ? 'positive'
                        : card.trend === 'down'
                        ? 'negative'
                        : 'stable'
                    }`}
                  >
                    {card.trend === 'up' && '↑'}
                    {card.trend === 'down' && '↓'}
                    {card.trend === 'stable' && '→'} {card.change}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Charts Section */}
      <section className="charts-section">
        <h2>Analytics Charts</h2>
        <div className="charts-container">
          <div className="chart-wrapper">
            <PriceChart
              data={priceData}
              isLoading={isLoading}
              period={period}
              eventType="prices"
            />
          </div>

          <div className="chart-wrapper">
            <AlertChart
              data={alertData}
              isLoading={isLoading}
              period={period}
              eventType="alerts"
            />
          </div>

          <div className="chart-wrapper">
            <AnomalyChart
              data={anomalyData}
              isLoading={isLoading}
              period={period}
              eventType="anomalies"
            />
          </div>

          <div className="chart-wrapper">
            <SignalChart
              data={signalData}
              isLoading={isLoading}
              period={period}
              eventType="signals"
            />
          </div>

          <div className="chart-wrapper">
            <TrendChart
              data={trendData}
              isLoading={isLoading}
              period={period}
              eventType="trends"
            />
          </div>
        </div>
      </section>

      {/* Supplier Scorecards */}
      <section className="scorecards-section">
        <h2>Supplier Performance</h2>
        <div className="scorecards-grid">
          {suppliers.map((supplier, idx) => (
            <div key={idx} className="scorecard">
              <h3>{supplier}</h3>
              <div className="scorecard-stats">
                <div className="scorecard-stat">
                  <span className="label">Score</span>
                  <span className="value">{85 + Math.floor(Math.random() * 15)}</span>
                </div>
                <div className="scorecard-stat">
                  <span className="label">Status</span>
                  <span className={`value status status-${['healthy', 'warning', 'critical'][Math.floor(Math.random() * 3)]}`}>
                    {['Healthy', 'At Risk', 'Critical'][Math.floor(Math.random() * 3)]}
                  </span>
                </div>
                <div className="scorecard-stat">
                  <span className="label">On-time</span>
                  <span className="value">{92 + Math.floor(Math.random() * 8)}%</span>
                </div>
                <div className="scorecard-stat">
                  <span className="label">Quality</span>
                  <span className="value">{88 + Math.floor(Math.random() * 12)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Data Export Section */}
      <section className="export-section">
        <h2>Export Data</h2>
        <p className="export-description">
          Download your analytics data in multiple formats. All exports include current filters and metadata.
        </p>
        <div className="export-buttons">
          <button 
            className="export-btn export-btn--csv"
            onClick={() => handleExport('csv')}
            title="Export all charts as comma-separated values"
            disabled={isLoading}
          >
            📥 Export as CSV
          </button>
          <button 
            className="export-btn export-btn--excel"
            onClick={() => handleExport('xlsx')}
            title="Export all charts as Excel spreadsheet"
            disabled={isLoading}
          >
            📊 Export as Excel
          </button>
          <button 
            className="export-btn export-btn--json"
            onClick={() => handleExport('json')}
            title="Export all charts as JSON format"
            disabled={isLoading}
          >
            📋 Export as JSON
          </button>
        </div>
        {exportMessage && (
          <div className={`export-message ${exportMessage.type}`}>
            {exportMessage.type === 'success' ? '✓' : '✕'} {exportMessage.text}
          </div>
        )}
      </section>
    </div>
  );
};

export default AnalyticsDashboard;

