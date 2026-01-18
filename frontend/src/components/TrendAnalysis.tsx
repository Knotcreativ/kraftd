/**
 * Trend Analysis Component
 * Displays real-time trend direction changes with confidence and forecasts
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket, TrendData } from '../hooks/useWebSocket';
import '../styles/TrendAnalysis.css';

export const TrendAnalysis: React.FC = () => {
  const [trends, setTrends] = useState<TrendChange[]>([]);
  const { isConnected, error, onMessage } = useWebSocket({
    topic: 'trends',
    autoConnect: true,
  });

  useEffect(() => {
    const unsubscribe = onMessage((event) => {
      if (event.type === 'trend_change') {
        const trendEvent = event as TrendChange;
        setTrends(prev => {
          // Keep most recent 20 trends
          const filtered = prev.filter(t => t.item_id !== trendEvent.item_id);
          return [trendEvent, ...filtered].slice(0, 20);
        });
      }
    });

    return unsubscribe;
  }, [onMessage]);

  const getTrendIcon = (direction: string) => {
    const iconMap: Record<string, string> = {
      UPTREND: '📈',
      DOWNTREND: '📉',
      STABLE: '➡️',
    };
    return iconMap[direction] || '?';
  };

  const getTrendColor = (direction: string) => {
    const colorMap: Record<string, string> = {
      UPTREND: '#2ecc71',
      DOWNTREND: '#e74c3c',
      STABLE: '#95a5a6',
    };
    return colorMap[direction] || '#95a5a6';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#2ecc71';
    if (confidence >= 0.6) return '#f39c12';
    return '#e74c3c';
  };

  return (
    <div className="trend-analysis">
      <div className="trends-header">
        <h2>📊 Trend Analysis</h2>
        <div className="trends-stats">
          <span className="stat">
            <strong>{trends.length}</strong> items tracked
          </span>
          <span className="stat">
            {isConnected ? '🟢 Live' : '🔴 Offline'}
          </span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {trends.length === 0 ? (
        <div className="empty-state">
          <p>📈 No trend changes detected</p>
          <p className="text-muted">Waiting for trend analysis data</p>
        </div>
      ) : (
        <div className="trends-grid">
          {trends.map((trend, index) => (
            <div
              key={index}
              className="trend-card"
              style={{ borderTopColor: getTrendColor(trend.trend_direction) }}
            >
              <div className="trend-header-row">
                <div className="trend-item-id">
                  <h4>{trend.item_id}</h4>
                </div>
                <div className="trend-direction-badge" style={{ backgroundColor: getTrendColor(trend.trend_direction) }}>
                  <span>{getTrendIcon(trend.trend_direction)}</span>
                  <span>{trend.trend_direction}</span>
                </div>
              </div>

              <div className="trend-message">
                {trend.message}
              </div>

              <div className="confidence-meter">
                <label>Confidence</label>
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{
                      width: (trend.confidence * 100) + '%',
                      backgroundColor: getConfidenceColor(trend.confidence),
                    }}
                  ></div>
                </div>
                <span className="confidence-value">{(trend.confidence * 100).toFixed(1)}%</span>
              </div>

              <div className="forecast-display">
                <div className="forecast-item">
                  <label>30-Day Forecast</label>
                  <div className="forecast-value">
                    ${trend.forecast_30d.toFixed(2)}
                  </div>
                </div>
              </div>

              <div className="trend-timestamp">
                🕐 {new Date(trend.timestamp).toLocaleString()}
              </div>

              {Object.keys(trend.details).length > 0 && (
                <div className="trend-details">
                  <details>
                    <summary>🔍 Details ({Object.keys(trend.details).length})</summary>
                    <div className="details-content">
                      {Object.entries(trend.details).map(([key, value]) => (
                        <div key={key} className="detail-row">
                          <span className="key">{key}:</span>
                          <span className="value">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
