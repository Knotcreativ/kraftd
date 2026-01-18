/**
 * Analytics Dashboard Page
 * Displays historical data with charts, filters, KPI cards, and data export
 */

import React, { useState, useEffect } from 'react';
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
  const [isLoading, setIsLoading] = useState(false);
  const [exportMessage, setExportMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Mock data generators - in production, these would fetch from API
  const generateMockData = (
    count: number = 30,
    baseValue: number = 100
  ): ChartDataPoint[] => {
    const data: ChartDataPoint[] = [];
    for (let i = 0; i < count; i++) {
      const date = new Date(filters.startDate);
      date.setDate(date.getDate() + i);
      
      const value = baseValue + Math.random() * 40 - 20;
      const trend = baseValue + (i * 0.5) + Math.random() * 20 - 10;
      
      data.push({
        date: date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        timestamp: date.getTime(),
        value: value,
        count: Math.floor(Math.random() * 50) + 5,
        avg: value + (Math.random() * 10 - 5),
        min: value - Math.random() * 10,
        max: value + Math.random() * 15,
        trend: trend,
        forecast: baseValue + (i * 0.7) + Math.random() * 25 - 12.5,
      });
    }
    return data;
  };

  // Sample KPI cards
  const kpiCards: KPICard[] = [
    {
      title: 'Total Alerts',
      value: 1247,
      change: '+12%',
      icon: '⚠️',
      color: 'red',
      trend: 'up',
    },
    {
      title: 'Avg Price',
      value: '$245.32',
      change: '+3.2%',
      icon: '💰',
      color: 'green',
      trend: 'up',
    },
    {
      title: 'Anomalies',
      value: 23,
      change: '-5%',
      icon: '🔍',
      color: 'orange',
      trend: 'down',
    },
    {
      title: 'Suppliers',
      value: 12,
      change: 'Stable',
      icon: '🏭',
      color: 'blue',
      trend: 'stable',
    },
  ];

  const items = ['Wheat', 'Corn', 'Soybeans', 'Coffee', 'Cocoa'];
  const suppliers = ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D', 'Supplier E'];

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    // Simulate loading data from API
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 500);
  };

  const handleExport = (format: 'csv' | 'xlsx' | 'json') => {
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
                <p className="kpi-value">{card.value}</p>
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
              data={generateMockData(30, 245)}
              isLoading={isLoading}
              period={period}
            />
          </div>

          <div className="chart-wrapper">
            <AlertChart
              data={generateMockData(30, 35)}
              isLoading={isLoading}
              period={period}
            />
          </div>

          <div className="chart-wrapper">
            <AnomalyChart
              data={generateMockData(30, 0.5)}
              isLoading={isLoading}
              period={period}
            />
          </div>

          <div className="chart-wrapper">
            <SignalChart
              data={generateMockData(30, 0.1)}
              isLoading={isLoading}
              period={period}
            />
          </div>

          <div className="chart-wrapper">
            <TrendChart
              data={generateMockData(30, 200)}
              isLoading={isLoading}
              period={period}
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
          >
            📥 Export as CSV
          </button>
          <button 
            className="export-btn export-btn--excel"
            onClick={() => handleExport('xlsx')}
            title="Export all charts as Excel spreadsheet"
          >
            📊 Export as Excel
          </button>
          <button 
            className="export-btn export-btn--json"
            onClick={() => handleExport('json')}
            title="Export all charts as JSON format"
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
      </section>
    </div>
  );
};

export default AnalyticsDashboard;
