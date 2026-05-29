/**
 * Bumblebee Food Cart - React hook for real-time order status updates via WebSocket.
 *
 * Connects to the backend WebSocket server and provides:
 * - Connection state (connecting, connected, disconnected, error)
 * - Latest order status updates
 * - Automatic reconnection with exponential backoff
 * - Channel-based subscriptions (orders, admin)
 */

import { useState, useEffect, useRef, useCallback } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Possible WebSocket connection states */
export type WebSocketState = "disconnected" | "connecting" | "connected" | "error";

/** Message types sent from the backend */
export interface OrderStatusMessage {
  type: "order_status_update";
  orderId: string;
  status: string;
  timestamp: string;
  customerName?: string;
  items?: Array<{ name: string; quantity: number }>;
}

export interface AdminNotificationMessage {
  type: "admin_notification";
  title: string;
  message: string;
  timestamp: string;
  severity?: "info" | "warning" | "error";
}

export interface GenericMessage {
  type: string;
  [key: string]: unknown;
}

export type WebSocketMessage = OrderStatusMessage | AdminNotificationMessage | GenericMessage;

/** Channel names for WebSocket subscriptions */
export type Channel = "orders" | "admin";

/** Configuration options for the WebSocket hook */
export interface UseWebSocketOptions {
  /** WebSocket URL (e.g., "ws://localhost:8000/ws/orders") */
  url: string;
  /** Reconnection delay in milliseconds (default: 3000) */
  reconnectDelay?: number;
  /** Maximum reconnection delay in milliseconds (default: 30000) */
  maxReconnectDelay?: number;
  /** Reconnection backoff multiplier (default: 1.5) */
  reconnectBackoffMultiplier?: number;
  /** Enable automatic reconnection (default: true) */
  autoReconnect?: boolean;
  /** Callback invoked when a message is received */
  onMessage?: (message: WebSocketMessage) => void;
  /** Callback invoked when connection state changes */
  onStateChange?: (state: WebSocketState) => void;
  /** Callback invoked when an error occurs */
  onError?: (error: Event) => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * React hook that manages a WebSocket connection for real-time order status updates.
 *
 * @param options - Configuration options for the WebSocket connection
 * @returns An object containing connection state, latest messages, and send function
 */
export function useOrderStatusWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    reconnectDelay: initialReconnectDelay = 3000,
    maxReconnectDelay = 30000,
    reconnectBackoffMultiplier = 1.5,
    autoReconnect = true,
    onMessage,
    onStateChange,
    onError,
  } = options;

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  const [state, setState] = useState<WebSocketState>("disconnected");
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [lastError, setLastError] = useState<Event | null>(null);

  // ---------------------------------------------------------------------------
  // Refs
  // ---------------------------------------------------------------------------

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectDelayRef = useRef<number>(initialReconnectDelay);
  const isMountedRef = useRef<boolean>(true);
  const reconnectAttemptRef = useRef<number>(0);

  // ---------------------------------------------------------------------------
  // Connection management
  // ---------------------------------------------------------------------------

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState("connecting");
    onStateChange?.("connecting");

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setState("connected");
        onStateChange?.("connected");
        // Reset reconnect delay on successful connection
        reconnectDelayRef.current = initialReconnectDelay;
        reconnectAttemptRef.current = 0;
      };

      ws.onmessage = (event: MessageEvent) => {
        if (!isMountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setMessages((prev) => [...prev.slice(-99), message]); // Keep last 100 messages
          onMessage?.(message);
        } catch (parseError) {
          console.error("Failed to parse WebSocket message:", parseError);
        }
      };

      ws.onerror = (event: Event) => {
        if (!isMountedRef.current) return;
        setLastError(event);
        onError?.(event);
      };

      ws.onclose = (event: CloseEvent) => {
        if (!isMountedRef.current) return;

        if (event.wasClean) {
          setState("disconnected");
          onStateChange?.("disconnected");
        } else {
          // Unexpected disconnection - attempt to reconnect
          setState("error");
          onStateChange?.("error");
          setLastError(new Event("disconnected"));

          if (autoReconnect) {
            attemptReconnect();
          }
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("WebSocket connection error:", error);
      setState("error");
      onStateChange?.("error");
      setLastError(error as Event);

      if (autoReconnect) {
        attemptReconnect();
      }
    }
  }, [url, initialReconnectDelay, autoReconnect, onStateChange, onMessage, onError]);

  const attemptReconnect = useCallback(() => {
    if (!isMountedRef.current || !autoReconnect) return;

    reconnectAttemptRef.current += 1;

    // Calculate exponential backoff delay
    const delay = Math.min(
      reconnectDelayRef.current * Math.pow(reconnectBackoffMultiplier, reconnectAttemptRef.current - 1),
      maxReconnectDelay,
    );

    reconnectDelayRef.current = delay;

    reconnectTimeoutRef.current = setTimeout(() => {
      if (isMountedRef.current) {
        connect();
      }
    }, delay);
  }, [autoReconnect, reconnectBackoffMultiplier, maxReconnectDelay, connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState("disconnected");
    onStateChange?.("disconnected");
  }, [onStateChange]);

  const send = useCallback(
    (data: Record<string, unknown>) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(data));
      }
    },
    [],
  );

  // ---------------------------------------------------------------------------
  // Effects
  // ---------------------------------------------------------------------------

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      disconnect();
    };
  }, [connect, disconnect]);

  // ---------------------------------------------------------------------------
  // Return
  // ---------------------------------------------------------------------------

  return {
    /** Current WebSocket connection state */
    state,
    /** Array of received messages (last 100) */
    messages,
    /** Most recent message received */
    lastMessage: messages.length > 0 ? messages[messages.length - 1] : null,
    /** Whether the connection is currently open */
    isConnected: state === "connected",
    /** Whether the connection is in the process of connecting */
    isConnecting: state === "connecting",
    /** The last error that occurred */
    lastError,
    /** Function to manually disconnect */
    disconnect,
    /** Function to send data to the server */
    send,
    /** Function to manually reconnect */
    reconnect: connect,
  };
}

export default useOrderStatusWebSocket;
