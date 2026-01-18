/**
 * Supplier Signals Component
 * Displays real-time supplier performance signals and health changes
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket, SupplierSignal } from '../hooks/useWebSocket';
import '../styles/SupplierSignals.css';

export const SupplierSignals: React.FC = () => {
  const [signals, setSignals] = useState<SupplierSignal[]>([]);
  const { isConnected, error, onMessage } = useWebSocket({
    topic: 'signals',
    autoConnect: true,
  });

  useEffect(() => {
    const unsubscribe = onMessage((event) => {
      if (event.type === 'supplier_signal') {
        const signalEvent = event as SupplierSignal;
        setSignals(prev => {
          // Keep most recent 25 signals
          const filtered = prev.filter(s => s.supplier_id !== signalEvent.supplier_id);
          return [signalEvent, ...filtered].slice(0, 25);
        });
      }
    });

    return unsubscribe;
  }, [onMessage]);

  const getSignalTypeEmoji = (type: string) => {
    const emojiMap: Record<string, string> = {
      HEALTH_CHANGE: '❤️',
      PERFORMANCE_ALERT: '⚡',
      RISK_FACTOR: '⚠️',
    };
    return emojiMap[type] || '📢';
  };

  const getSignalTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      HEALTH_CHANGE: '#2ecc71',
      PERFORMANCE_ALERT: '#f39c12',
      RISK_FACTOR: '#e74c3c',
    };
    return colorMap[type] || '#95a5a6';
  };

  return (
    <div className="supplier-signals">
      <div className="signals-header">
        <h2>🏭 Supplier Signals</h2>
        <div className="signals-stats">
          <span className="stat">
            <strong>{signals.length}</strong> signals
          </span>
          <span className="stat">
            {isConnected ? '🟢 Live' : '🔴 Offline'}
          </span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {signals.length === 0 ? (
        <div className="empty-state">
          <p>📊 No supplier signals received</p>
          <p className="text-muted">Waiting for supplier performance data</p>
        </div>
      ) : (
        <div className="signals-list">
          {signals.map((signal, index) => (
            <div
              key={index}
              className="signal-card"
              style={{ borderLeftColor: getSignalTypeColor(signal.signal_type) }}
            >
              <div className="signal-top">
                <div className="signal-type-badge">
                  <span className="emoji">{getSignalTypeEmoji(signal.signal_type)}</span>
                  <span className="type-label">{signal.signal_type}</span>
                </div>
                <span className="supplier-id">🏷️ {signal.supplier_id}</span>
              </div>

              <div className="signal-message">
                {signal.message}
              </div>

              <div className="signal-values">
                {signal.old_value !== undefined && signal.new_value !== undefined && (
                  <div className="value-change">
                    <div className="value-item">
                      <label>Old Value</label>
                      <code>{JSON.stringify(signal.old_value)}</code>
                    </div>
                    <div className="arrow">→</div>
                    <div className="value-item">
                      <label>New Value</label>
                      <code>{JSON.stringify(signal.new_value)}</code>
                    </div>
                  </div>
                )}
              </div>

              <div className="signal-timestamp">
                🕐 {new Date(signal.timestamp).toLocaleString()}
              </div>

              {Object.keys(signal.details).length > 0 && (
                <div className="signal-details">
                  <details>
                    <summary>📋 Details ({Object.keys(signal.details).length})</summary>
                    <div className="details-content">
                      {Object.entries(signal.details).map(([key, value]) => (
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
