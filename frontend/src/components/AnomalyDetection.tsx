/**
 * Anomaly Detection Component
 * Displays detected statistical anomalies with severity and details
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket, AnomalyDetected } from '../../hooks/useWebSocket';
import '../styles/AnomalyDetection.css';

export const AnomalyDetection: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AnomalyDetected[]>([]);
  const { isConnected, error, onMessage } = useWebSocket({
    topic: 'anomalies',
    autoConnect: true,
  });

  useEffect(() => {
    const unsubscribe = onMessage((event) => {
      if (event.type === 'anomaly_detected') {
        const anomalyEvent = event as AnomalyDetected;
        setAnomalies(prev => {
          // Keep most recent 30 anomalies
          const filtered = prev.filter(a => a.anomaly_id !== anomalyEvent.anomaly_id);
          return [anomalyEvent, ...filtered].slice(0, 30);
        });
      }
    });

    return unsubscribe;
  }, [onMessage]);

  const getSeverityColor = (severity: string) => {
    const colorMap: Record<string, string> = {
      CRITICAL: '#e74c3c',
      HIGH: '#e67e22',
      MEDIUM: '#f39c12',
      LOW: '#3498db',
    };
    return colorMap[severity] || '#95a5a6';
  };

  const getSeverityIcon = (severity: string) => {
    const iconMap: Record<string, string> = {
      CRITICAL: '🔴',
      HIGH: '🟠',
      MEDIUM: '🟡',
      LOW: '🔵',
    };
    return iconMap[severity] || '⚪';
  };

  const getAnomalyTypeEmoji = (type: string) => {
    const emojiMap: Record<string, string> = {
      PRICE_ANOMALY: '💹',
      TREND_BREAK: '⚡',
      SUPPLIER_ANOMALY: '🏭',
      VOLATILITY_SPIKE: '🌪️',
    };
    return emojiMap[type] || '🔍';
  };

  return (
    <div className="anomaly-detection">
      <div className="anomaly-header">
        <h2>🔍 Anomaly Detection</h2>
        <div className="anomaly-stats">
          <span className="stat">
            <strong>{anomalies.length}</strong> detected
          </span>
          <span className="stat">
            {isConnected ? '🟢 Live' : '🔴 Offline'}
          </span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {anomalies.length === 0 ? (
        <div className="empty-state">
          <p>✅ No anomalies detected</p>
          <p className="text-muted">System is monitoring normally</p>
        </div>
      ) : (
        <div className="anomalies-list">
          {anomalies.map(anomaly => (
            <div
              key={anomaly.anomaly_id}
              className="anomaly-card"
              style={{ borderTopColor: getSeverityColor(anomaly.severity) }}
            >
              <div className="anomaly-header-row">
                <div className="anomaly-type">
                  <span className="emoji">{getAnomalyTypeEmoji(anomaly.anomaly_type)}</span>
                  <span className="type-label">{anomaly.anomaly_type}</span>
                </div>
                <div className="severity-badge" style={{ backgroundColor: getSeverityColor(anomaly.severity) }}>
                  {getSeverityIcon(anomaly.severity)} {anomaly.severity}
                </div>
              </div>

              <div className="anomaly-message">
                {anomaly.message}
              </div>

              <div className="z-score-display">
                <div className="z-score-bar">
                  <div className="z-score-value">
                    <strong>Z-Score: {anomaly.z_score.toFixed(2)}</strong>
                    <span className="z-score-threshold">Threshold: ±2.5</span>
                  </div>
                  <div className="z-score-visual">
                    <div
                      className="z-score-indicator"
                      style={{
                        width: Math.min(Math.abs(anomaly.z_score) * 10, 100) + '%',
                        backgroundColor: getSeverityColor(anomaly.severity),
                      }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="anomaly-details">
                {anomaly.item_id && (
                  <span className="detail">📦 Item: {anomaly.item_id}</span>
                )}
                {anomaly.supplier_id && (
                  <span className="detail">🏭 Supplier: {anomaly.supplier_id}</span>
                )}
                <span className="detail">🕐 {new Date(anomaly.timestamp).toLocaleTimeString()}</span>
              </div>

              {Object.keys(anomaly.details).length > 0 && (
                <div className="anomaly-extra-details">
                  <details>
                    <summary>📊 Details ({Object.keys(anomaly.details).length})</summary>
                    <div className="details-content">
                      {Object.entries(anomaly.details).map(([key, value]) => (
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

              <div className="anomaly-id">ID: {anomaly.anomaly_id.slice(-8)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
