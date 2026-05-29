import { useState, useEffect, useCallback, useRef } from "react";
import { useOrderStatusWebSocket, OrderStatusMessage } from "../hooks/useOrderStatusWebSocket";
import { OrderStatus as OrderStatusType } from "../types/shared";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_FLOW: OrderStatusType[] = [
  "pending",
  "confirmed",
  "preparing",
  "ready",
  "delivered",
];

const STATUS_LABELS: Record<OrderStatusType, string> = {
  pending: "Order Placed",
  confirmed: "Confirmed",
  preparing: "Preparing",
  ready: "Ready for Pickup",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

const STATUS_ICONS: Record<OrderStatusType, string> = {
  pending: "📋",
  confirmed: "✅",
  preparing: "🍳",
  ready: "🎉",
  delivered: "🚗",
  cancelled: "❌",
};

const STATUS_COLORS: Record<OrderStatusType, string> = {
  pending: "var(--color-warning)",
  confirmed: "var(--color-info)",
  preparing: "var(--color-primary)",
  ready: "var(--color-success)",
  delivered: "var(--color-success)",
  cancelled: "var(--color-error)",
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusTimeline({
  currentStatus,
}: {
  currentStatus: OrderStatusType | null;
}) {
  const currentIndex = STATUS_FLOW.indexOf(currentStatus as OrderStatusType);

  return (
    <div className="status-timeline">
      {STATUS_FLOW.map((status, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;
        const isUpcoming = index > currentIndex;
        const isActive = isCurrent || isCompleted;

        return (
          <div key={status} className="status-step">
            <div
              className={`status-step-indicator ${isCompleted ? "completed" : ""} ${
                isCurrent ? "current" : ""
              }`}
              style={{
                borderColor: isCompleted
                  ? "var(--color-success)"
                  : isCurrent
                    ? STATUS_COLORS[status]
                    : "var(--border-color)",
                backgroundColor: isCompleted
                  ? "var(--color-success)"
                  : isCurrent
                    ? "var(--bg-card)"
                    : "var(--bg-card)",
              }}
            >
              {isCompleted ? "✓" : STATUS_ICONS[status]}
            </div>
            <div
              className={`status-step-label ${isActive ? "active" : ""}`}
              style={{
                color: isActive ? "var(--text-primary)" : "var(--text-muted)",
              }}
            >
              {STATUS_LABELS[status]}
            </div>
            {index < STATUS_FLOW.length - 1 && (
              <div
                className={`status-connector ${isCompleted ? "completed" : ""}`}
                style={{
                  backgroundColor: isCompleted
                    ? "var(--color-success)"
                    : "var(--border-color)",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StatusDetailCard({
  status,
  lastUpdate,
  orderId,
}: {
  status: OrderStatusType | null;
  lastUpdate: string | null;
  orderId: string;
}) {
  if (!status) {
    return (
      <div className="status-detail-card">
        <p className="status-detail-text" style={{ color: "var(--text-muted)" }}>
          Enter an order number to track its status.
        </p>
      </div>
    );
  }

  return (
    <div className="status-detail-card">
      <div className="status-detail-header">
        <span
          className="status-badge"
          style={{
            backgroundColor: STATUS_COLORS[status],
            color: "var(--text-on-primary)",
          }}
        >
          {STATUS_ICONS[status]} {STATUS_LABELS[status]}
        </span>
      </div>
      <div className="status-detail-body">
        <p className="status-detail-text">
          <strong>Order ID:</strong> {orderId}
        </p>
        {lastUpdate && (
          <p className="status-detail-text">
            <strong>Last Updated:</strong>{" "}
            {new Date(lastUpdate).toLocaleString()}
          </p>
        )}
        <p className="status-detail-text">
          <strong>Current Stage:</strong>{" "}
          {STATUS_LABELS[status] || status}
        </p>
      </div>
    </div>
  );
}

function ConnectionIndicator({
  state,
}: {
  state: "disconnected" | "connecting" | "connected" | "error";
}) {
  const config = {
    disconnected: {
      label: "Disconnected",
      color: "var(--text-muted)",
      dotColor: "var(--text-muted)",
    },
    connecting: {
      label: "Connecting...",
      color: "var(--color-warning)",
      dotColor: "var(--color-warning)",
    },
    connected: {
      label: "Connected",
      color: "var(--color-success)",
      dotColor: "var(--color-success)",
    },
    error: {
      label: "Connection Error",
      color: "var(--color-error)",
      dotColor: "var(--color-error)",
    },
  };

  const { label, color, dotColor } = config[state];

  return (
    <div className="connection-indicator">
      <span
        className="connection-dot"
        style={{
          backgroundColor: dotColor,
          animation: state === "connecting" ? "pulse 1.5s infinite" : "none",
        }}
      />
      <span style={{ color }}>{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function OrderStatus() {
  const [orderId, setOrderId] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [currentStatus, setCurrentStatus] = useState<OrderStatusType | null>(
    null
  );
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [connectionState, setConnectionState] = useState<
    "disconnected" | "connecting" | "connected" | "error"
  >("disconnected");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusHistory, setStatusHistory] = useState<OrderStatusMessage[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleWebSocketMessage = useCallback(
    (message: OrderStatusMessage) => {
      if (message.orderId === orderId) {
        setCurrentStatus(message.status as OrderStatusType);
        setLastUpdate(message.timestamp);
        setStatusHistory((prev) => [...prev, message]);
        setErrorMessage(null);
      }
    },
    [orderId]
  );

  const handleConnectionStateChange = useCallback(
    (state: "disconnected" | "connecting" | "connected" | "error") => {
      setConnectionState(state);
      if (state === "error") {
        setErrorMessage("WebSocket connection failed. Please try again.");
      }
    },
    []
  );

  const { connect, disconnect } = useOrderStatusWebSocket({
    url: `ws://localhost:8000/ws/orders`,
    onMessage: handleWebSocketMessage,
    onStateChange: handleConnectionStateChange,
    autoReconnect: true,
    reconnectDelay: 3000,
    maxReconnectDelay: 30000,
    reconnectBackoffMultiplier: 1.5,
  });

  useEffect(() => {
    if (orderId) {
      connect();
    } else {
      disconnect();
      setCurrentStatus(null);
      setLastUpdate(null);
      setStatusHistory([]);
    }

    return () => {
      disconnect();
    };
  }, [orderId, connect, disconnect]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed) {
      setOrderId(trimmed);
      setErrorMessage(null);
      setCurrentStatus(null);
      setLastUpdate(null);
      setStatusHistory([]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleClear = () => {
    setInputValue("");
    setOrderId("");
    setCurrentStatus(null);
    setLastUpdate(null);
    setStatusHistory([]);
    setErrorMessage(null);
    inputRef.current?.focus();
  };

  return (
    <div className="order-status-page">
      <div className="order-status-container">
        <header className="order-status-header">
          <h1 className="order-status-title">Order Status</h1>
          <p className="order-status-subtitle">
            Track your order in real-time
          </p>
        </header>

        <form className="order-search-form" onSubmit={handleSubmit}>
          <div className="order-input-group">
            <input
              ref={inputRef}
              type="text"
              className="order-input"
              placeholder="Enter your order number"
              value={inputValue}
              onChange={handleInputChange}
              aria-label="Order number"
            />
            <button
              type="submit"
              className="order-search-button"
              style={{
                backgroundColor: "var(--color-primary)",
                color: "var(--text-on-primary)",
              }}
              disabled={!inputValue.trim()}
            >
              Track Order
            </button>
          </div>
          {orderId && (
            <button
              type="button"
              className="order-clear-button"
              onClick={handleClear}
            >
              Clear
            </button>
          )}
        </form>

        {errorMessage && (
          <div
            className="error-message"
            style={{
              backgroundColor: "var(--bg-error)",
              color: "var(--color-error)",
              borderColor: "var(--color-error)",
            }}
          >
            {errorMessage}
          </div>
        )}

        <ConnectionIndicator state={connectionState} />

        {orderId && (
          <>
            <StatusTimeline currentStatus={currentStatus} />
            <StatusDetailCard
              status={currentStatus}
              lastUpdate={lastUpdate}
              orderId={orderId}
            />

            {statusHistory.length > 0 && (
              <div className="status-history">
                <h2 className="status-history-title">Status History</h2>
                <div className="status-history-list">
                  {statusHistory
                    .slice()
                    .reverse()
                    .map((msg, index) => (
                      <div
                        key={index}
                        className="status-history-item"
                        style={{
                          borderColor: STATUS_COLORS[msg.status as OrderStatusType],
                        }}
                      >
                        <div className="status-history-item-header">
                          <span
                            className="status-history-item-status"
                            style={{
                              backgroundColor: STATUS_COLORS[
                                msg.status as OrderStatusType
                              ],
                              color: "var(--text-on-primary)",
                            }}
                          >
                            {STATUS_ICONS[msg.status as OrderStatusType]}{" "}
                            {STATUS_LABELS[msg.status as OrderStatusType]}
                          </span>
                          <span className="status-history-item-time">
                            {new Date(msg.timestamp).toLocaleString()}
                          </span>
                        </div>
                        {msg.customerName && (
                          <p className="status-history-item-detail">
                            Customer: {msg.customerName}
                          </p>
                        )}
                        {msg.items && msg.items.length > 0 && (
                          <ul className="status-history-item-items">
                            {msg.items.map((item, i) => (
                              <li key={i} className="status-history-item-item">
                                {item.quantity}x {item.name}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            )}
          </>
        )}

        {!orderId && (
          <div className="order-status-empty">
            <p className="order-status-empty-text">
              Enter your order number above to start tracking.
            </p>
            <p className="order-status-empty-hint">
              You can find your order number in your confirmation email or
              receipt.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
