import React, { useState } from 'react';
import Breadcrumb from '../components/Breadcrumb';
import FilterPanel from '../components/FilterPanel';
import './AnalyticsPage.css';

type AnalyticsView = 'overview' | 'charts';

/**
 * Analytics Page
 * Comprehensive analytics dashboard with charts and filters
 */
const AnalyticsPage: React.FC = () => {
  const [activeView, setActiveView] = useState<AnalyticsView>('overview');
  const [showFilters, setShowFilters] = useState(true);

  return (
    <div className="analytics-page">
      <Breadcrumb />

      <div className="analytics-container">
        {/* Header */}
        <div className="analytics-header">
          <div className="header-content">
            <h1 className="analytics-title">📈 Analytics</h1>
            <p className="analytics-subtitle">
              Advanced analytics, trends, and insights for your supply chain
            </p>
          </div>

          <div className="header-controls">
            <button
              className={`view-toggle ${activeView === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveView('overview')}
              title="Overview"
            >
              📊 Overview
            </button>
            <button
              className={`view-toggle ${activeView === 'charts' ? 'active' : ''}`}
              onClick={() => setActiveView('charts')}
              title="Charts"
            >
              📈 Charts
            </button>
            <button
              className="filter-toggle"
              onClick={() => setShowFilters(!showFilters)}
              title="Toggle Filters"
            >
              {showFilters ? '🔽' : '▶️'} Filters
            </button>
          </div>
        </div>

        <div className="analytics-layout">
          {/* Filter Panel */}
          {showFilters && (
            <aside className="analytics-sidebar">
              <FilterPanel />
            </aside>
          )}

          {/* Main Content */}
          <main className="analytics-main">
            {activeView === 'overview' && (
              <div className="analytics-view">
                <section className="analytics-section">
                  <h2>Key Metrics Overview</h2>
                  <div className="placeholder">Analytics overview coming soon</div>
                </section>
              </div>
            )}

            {activeView === 'charts' && (
              <div className="analytics-view">
                <section className="analytics-section">
                  <h2>Detailed Charts & Visualizations</h2>
                  <div className="placeholder">Analytics charts coming soon</div>
                </section>
              </div>
            )}
          </main>
        </div>

        {/* Footer Info */}
        <div className="analytics-footer">
          <p className="footer-info">
            💡 Tip: Use filters to narrow down data. Click export button to download results.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
