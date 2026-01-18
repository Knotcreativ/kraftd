/**
 * React Hook for WebSocket Real-Time Streaming
 * Handles connection, reconnection, and event subscription
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuth } from '../context/AuthContext';

// Event type definitions from backend
export interface PriceUpdate {
  type: 'price_update';
  timestamp: string;
  item_id: string;
  price: number;
  previous_price: number | null;
  change_percent: number;
  trend_direction: 'UPTREND' | 'DOWNTREND' | 'STABLE';
  volatility: number;
  moving_average_7d: number;
  moving_average_30d: number;
}

export interface RiskAlert {
  type: 'risk_alert';
  alert_id: string;
  timestamp: string;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  alert_type: string;
  item_id?: string;
  supplier_id?: string;
  message: string;
  details: Record<string, any>;
  acknowledged: boolean;
}

export interface SupplierSignal {
  type: 'supplier_signal';
  timestamp: string;
  supplier_id: string;
  signal_type: 'HEALTH_CHANGE' | 'PERFORMANCE_ALERT' | 'RISK_FACTOR';
  old_value?: any;
  new_value?: any;
  message: string;
  details: Record<string, any>;
}

export interface AnomalyDetected {
  type: 'anomaly_detected';
  anomaly_id: string;
  timestamp: string;
  anomaly_type: 'PRICE_ANOMALY' | 'TREND_BREAK' | 'SUPPLIER_ANOMALY' | 'VOLATILITY_SPIKE';
  item_id?: string;
  supplier_id?: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  z_score: number;
  message: string;
  details: Record<string, any>;
}

export interface TrendChange {
  type: 'trend_change';
  timestamp: string;
  item_id: string;
  trend_direction: 'UPTREND' | 'DOWNTREND' | 'STABLE';
  confidence: number;
  forecast_30d: number;
  message: string;
  details: Record<string, any>;
}

export interface HealthCheck {
  type: 'health_check';
  timestamp: string;
  server_time: string;
  active_connections: number;
  uptime_seconds: number;
}

export type StreamEvent = 
  | PriceUpdate 
  | RiskAlert 
  | SupplierSignal 
  | AnomalyDetected 
  | TrendChange 
  | HealthCheck;

export interface WebSocketHookOptions {
  url?: string;
  topic: string;
  filters?: Record<string, any>;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export interface WebSocketHookState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  events: StreamEvent[];
  lastEvent: StreamEvent | null;
  reconnectAttempts: number;
  messageCount: number;
}

/**
 * Hook for consuming real-time WebSocket streams
 * Automatically handles auth, connection, and reconnection
 */
export const useWebSocket = (options: WebSocketHookOptions) => {
  const { token } = useAuth();
  const [state, setState] = useState<WebSocketHookState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    events: [],
    lastEvent: null,
    reconnectAttempts: 0,
    messageCount: 0,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageListenersRef = useRef<Set<(event: StreamEvent) => void>>(new Set());

  const {
    url = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/ws/${options.topic}`,
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(async () => {
    if (!token) {
      setState(prev => ({ ...prev, error: 'No authentication token available' }));
      return;
    }

    if (state.isConnecting || state.isConnected) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const wsUrl = new URL(url, window.location.origin);
      wsUrl.searchParams.append('token', token);

      const ws = new WebSocket(wsUrl.toString());

      ws.onopen = () => {
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          reconnectAttempts: 0,
          error: null,
        }));

        // Send subscription message if filters provided
        if (options.filters) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            filters: options.filters,
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const streamEvent = message as StreamEvent;

          setState(prev => ({
            ...prev,
            events: [streamEvent, ...prev.events.slice(0, 99)], // Keep last 100
            lastEvent: streamEvent,
            messageCount: prev.messageCount + 1,
          }));

          // Notify all listeners
          messageListenersRef.current.forEach(listener => {
            try {
              listener(streamEvent);
            } catch (err) {
              console.error('Error in message listener:', err);
            }
          });
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false,
        }));
      };

      ws.onclose = () => {
        wsRef.current = null;
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));

        // Attempt reconnection
        if (state.reconnectAttempts < reconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setState(prev => ({
              ...prev,
              reconnectAttempts: prev.reconnectAttempts + 1,
            }));
            connect();
          }, reconnectInterval);
        } else {
          setState(prev => ({
            ...prev,
            error: `Failed to connect after ${reconnectAttempts} attempts`,
          }));
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: err instanceof Error ? err.message : 'Connection failed',
      }));
    }
  }, [token, url, options.filters, state.reconnectAttempts, reconnectAttempts, reconnectInterval, state.isConnecting, state.isConnected]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  }, []);

  /**
   * Subscribe to specific event type
   */
  const onMessage = useCallback((callback: (event: StreamEvent) => void) => {
    messageListenersRef.current.add(callback);
    return () => {
      messageListenersRef.current.delete(callback);
    };
  }, []);

  /**
   * Clear event history
   */
  const clearEvents = useCallback(() => {
    setState(prev => ({
      ...prev,
      events: [],
      lastEvent: null,
    }));
  }, []);

  /**
   * Auto-connect on mount
   */
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, token, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    onMessage,
    clearEvents,
    isReady: state.isConnected && !state.isConnecting,
  };
};
