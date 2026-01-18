/**
 * Risk Alerts Component
 * Displays real-time risk alerts with severity levels
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket, RiskAlert } from '../hooks/useWebSocket';
import '../styles/RiskAlerts.css';

export const RiskAlerts: React.FC = () => {
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());
  const { isConnected, error, onMessage } = useWebSocket({
    topic: 'alerts',
    autoConnect: true,
  });

  useEffect(() => {
    const unsubscribe = onMessage((event) => {
      if (event.type === 'risk_alert') {
        const alertEvent = event as RiskAlert;
        setAlerts(prev => {
          // Keep most recent 50 alerts
          const filtered = prev.filter(a => a.alert_id !== alertEvent.alert_id);
          return [alertEvent, ...filtered].slice(0, 50);
        });
      }
    });

    return unsubscribe;
  }, [onMessage]);

  const dismissAlert = (alertId: string) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
    setAlerts(prev => prev.filter(a => a.alert_id !== alertId));
  };

  const getRiskLevelIcon = (level: string) => {
    const iconMap: Record<string, string> = {
      CRITICAL: '🚨',
      HIGH: '⚠️',
      MEDIUM: '⚡',
      LOW: 'ℹ️',
    };
    return iconMap[level] || 'ℹ️';
  };

  const getRiskLevelColor = (level: string) => {
    const colorMap: Record<string, string> = {
      CRITICAL: '#e74c3c',
      HIGH: '#e67e22',
      MEDIUM: '#f39c12',
      LOW: '#3498db',
    };
    return colorMap[level] || '#95a5a6';
  };

  const activeAlerts = alerts.filter(a => !dismissedAlerts.has(a.alert_id));

  return (
    <div className="risk-alerts">
      <div className="alerts-header">
        <h2>⚠️ Risk Alerts</h2>
        <div className="alert-stats">
          <span className="count-badge critical">
            {activeAlerts.filter(a => a.risk_level === 'CRITICAL').length} Critical
          </span>
          <span className="count-badge high">
            {activeAlerts.filter(a => a.risk_level === 'HIGH').length} High
          </span>
          <span className="count-badge medium">
            {activeAlerts.filter(a => a.risk_level === 'MEDIUM').length} Medium
          </span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {activeAlerts.length === 0 ? (
        <div className="empty-state">
          <p>✅ No active risk alerts</p>
          <p className="text-muted">Connection: {isConnected ? 'Live' : 'Offline'}</p>
        </div>
      ) : (
        <div className="alerts-list">
          {activeAlerts.map(alert => (
            <div
              key={alert.alert_id}
              className="alert-item"
              style={{ borderLeftColor: getRiskLevelColor(alert.risk_level) }}
            >
              <div className="alert-top">
                <div className="alert-icon-title">
                  <span className="alert-icon">
                    {getRiskLevelIcon(alert.risk_level)}
                  </span>
                  <div className="alert-title-info">
                    <h4>{alert.message}</h4>
                    <p className="alert-type">{alert.alert_type}</p>
                  </div>
                </div>
                <button
                  className="dismiss-button"
                  onClick={() => dismissAlert(alert.alert_id)}
                  title="Dismiss alert"
                >
                  ✕
                </button>
              </div>

              <div className="alert-details">
                {alert.item_id && (
                  <span className="detail">📦 Item: {alert.item_id}</span>
                )}
                {alert.supplier_id && (
                  <span className="detail">🏭 Supplier: {alert.supplier_id}</span>
                )}
                <span className="detail">🕐 {new Date(alert.timestamp).toLocaleTimeString()}</span>
              </div>

              {Object.keys(alert.details).length > 0 && (
                <div className="alert-extras">
                  {Object.entries(alert.details).slice(0, 2).map(([key, value]) => (
                    <div key={key} className="extra-item">
                      <span className="key">{key}:</span>
                      <span className="value">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div className="alert-id">#{alert.alert_id.slice(-8)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
