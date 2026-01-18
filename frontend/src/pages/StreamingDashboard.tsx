/**
 * Main Streaming Dashboard Page
 * Integrates all real-time data components with layout and navigation
 */

import React, { useState } from 'react';
import { PriceDashboard } from '../components/PriceDashboard';
import { RiskAlerts } from '../components/RiskAlerts';
import { AnomalyDetection } from '../components/AnomalyDetection';
import { SupplierSignals } from '../components/SupplierSignals';
import { TrendAnalysis } from '../components/TrendAnalysis';
import FilterPanel from '../components/FilterPanel';
import '../styles/StreamingDashboard.css';

type DashboardTab = 'overview' | 'prices' | 'alerts' | 'anomalies' | 'signals' | 'trends';

interface FilterState {
  startDate: Date;
  endDate: Date;
  itemId?: string;
  supplierId?: string;
  severity?: string;
  riskLevel?: string;
  displayMode: 'compact' | 'expanded';
}

export const StreamingDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [filters, setFilters] = useState<FilterState>({
    startDate: new Date(new Date().setDate(new Date().getDate() - 30)),
    endDate: new Date(),
    displayMode: 'compact',
  });

  // Sample data - in production, this would come from API based on filters
  const items = ['Wheat', 'Corn', 'Soybeans', 'Coffee', 'Cocoa'];
  const suppliers = ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D', 'Supplier E'];

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    // TODO: Use newFilters to query historical data from /api/v1/events/*
    console.log('Filters updated:', newFilters);
  };

  const tabs: Array<{ id: DashboardTab; label: string; icon: string }> = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'prices', label: 'Prices', icon: '💰' },
    { id: 'alerts', label: 'Risk Alerts', icon: '⚠️' },
    { id: 'anomalies', label: 'Anomalies', icon: '🔍' },
    { id: 'signals', label: 'Supplier Signals', icon: '🏭' },
    { id: 'trends', label: 'Trends', icon: '📈' },
  ];

  return (
    <div className="streaming-dashboard-page">
      <header className="dashboard-page-header">
        <div className="header-content">
          <h1>📡 Real-Time Supply Chain Intelligence</h1>
          <p>Live monitoring of prices, risks, anomalies, and market trends</p>
        </div>
      </header>

      <nav className="dashboard-nav-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      <FilterPanel 
        onFilterChange={handleFilterChange}
        items={items}
        suppliers={suppliers}
      />

      <main className="dashboard-content">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'prices' && <PriceDashboard />}
        {activeTab === 'alerts' && <RiskAlerts />}
        {activeTab === 'anomalies' && <AnomalyDetection />}
        {activeTab === 'signals' && <SupplierSignals />}
        {activeTab === 'trends' && <TrendAnalysis />}
      </main>
    </div>
  );
};

/**
 * Overview Tab - Shows summary of all streams
 */
const OverviewTab: React.FC = () => {
  const [displayMode, setDisplayMode] = useState<'minimal' | 'compact'>('minimal');

  return (
    <div className="overview-tab">
      <div className="overview-controls">
        <div className="display-mode-selector">
          <label>View Mode:</label>
          <button
            className={displayMode === 'minimal' ? 'active' : ''}
            onClick={() => setDisplayMode('minimal')}
          >
            Minimal
          </button>
          <button
            className={displayMode === 'compact' ? 'active' : ''}
            onClick={() => setDisplayMode('compact')}
          >
            Compact
          </button>
        </div>
      </div>

      <div className={`overview-grid overview-${displayMode}`}>
        <section className="overview-section">
          <h2>💰 Price Dashboard</h2>
          <p>Real-time commodity prices with technical indicators</p>
          <PriceDashboard />
        </section>

        <section className="overview-section">
          <h2>⚠️ Risk Alerts</h2>
          <p>Critical risk threshold breaches and warnings</p>
          <RiskAlerts />
        </section>

        <section className="overview-section">
          <h2>🔍 Anomalies</h2>
          <p>Statistical anomalies and outliers detected</p>
          <AnomalyDetection />
        </section>

        <section className="overview-section">
          <h2>🏭 Supplier Signals</h2>
          <p>Supplier performance and health changes</p>
          <SupplierSignals />
        </section>

        <section className="overview-section">
          <h2>📈 Trends</h2>
          <p>Market trend analysis and forecasts</p>
          <TrendAnalysis />
        </section>
      </div>
    </div>
  );
};
