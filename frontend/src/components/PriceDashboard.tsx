/**
 * Price Dashboard Component
 * Displays real-time commodity prices with trends and technical indicators
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket, PriceUpdate } from '../hooks/useWebSocket';
import '../styles/PriceDashboard.css';

interface PriceData {
  [itemId: string]: PriceUpdate;
}

export const PriceDashboard: React.FC = () => {
  const [prices, setPrices] = useState<PriceData>({});
  const { isConnected, error, lastEvent, onMessage, messageCount } = useWebSocket({
    topic: 'prices',
    autoConnect: true,
  });

  useEffect(() => {
    const unsubscribe = onMessage((event) => {
      if (event.type === 'price_update') {
        const priceEvent = event as PriceUpdate;
        setPrices(prev => ({
          ...prev,
          [priceEvent.item_id]: priceEvent,
        }));
      }
    });

    return unsubscribe;
  }, [onMessage]);

  const trendIcon = (direction: string) => {
    switch (direction) {
      case 'UPTREND':
        return '📈';
      case 'DOWNTREND':
        return '📉';
      default:
        return '➡️';
    }
  };

  const trendColor = (direction: string) => {
    switch (direction) {
      case 'UPTREND':
        return '#2ecc71';
      case 'DOWNTREND':
        return '#e74c3c';
      default:
        return '#95a5a6';
    }
  };

  return (
    <div className="price-dashboard">
      <div className="dashboard-header">
        <h2>💰 Real-Time Prices</h2>
        <div className="connection-badge">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span>{isConnected ? 'Live' : 'Offline'}</span>
          <span className="message-count">{messageCount} updates</span>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {Object.keys(prices).length === 0 ? (
        <div className="empty-state">
          <p>Waiting for price updates...</p>
          <p className="text-muted">Connected: {isConnected ? 'Yes' : 'No'}</p>
        </div>
      ) : (
        <div className="price-grid">
          {Object.entries(prices).map(([itemId, price]) => (
            <div key={itemId} className="price-card">
              <div className="price-header">
                <h3>{price.item_id}</h3>
                <span 
                  className="trend-indicator"
                  style={{ color: trendColor(price.trend_direction) }}
                >
                  {trendIcon(price.trend_direction)} {price.trend_direction}
                </span>
              </div>

              <div className="price-display">
                <div className="current-price">
                  ${price.price.toFixed(2)}
                </div>
                <div className="price-change">
                  <span className={price.change_percent >= 0 ? 'positive' : 'negative'}>
                    {price.change_percent >= 0 ? '+' : ''}{price.change_percent.toFixed(2)}%
                  </span>
                  {price.previous_price && (
                    <span className="previous-price">
                      from ${price.previous_price.toFixed(2)}
                    </span>
                  )}
                </div>
              </div>

              <div className="technical-indicators">
                <div className="indicator">
                  <label>7D MA</label>
                  <div className="value">${price.moving_average_7d.toFixed(2)}</div>
                </div>
                <div className="indicator">
                  <label>30D MA</label>
                  <div className="value">${price.moving_average_30d.toFixed(2)}</div>
                </div>
                <div className="indicator">
                  <label>Volatility</label>
                  <div className="value">{price.volatility.toFixed(2)}%</div>
                </div>
              </div>

              <div className="timestamp">
                {new Date(price.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
