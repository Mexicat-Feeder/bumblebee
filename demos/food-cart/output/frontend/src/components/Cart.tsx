/**
 * Cart - Customer cart component.
 * Allows customers to view cart items, adjust quantities, and see the total.
 */

import { useState, useEffect, useCallback } from "react";
import { OrderItem } from "../types/shared";

// ---------------------------------------------------------------------------
// Cart context / storage helpers
// ---------------------------------------------------------------------------

const CART_STORAGE_KEY = "bumblebee-cart";

function loadCart(): OrderItem[] {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function saveCart(cart: OrderItem[]): void {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  } catch {
    // storage full or unavailable – silently ignore
  }
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/**
 * Renders a single cart line item with quantity controls.
 */
function CartItemRow({
  item,
  onUpdateQuantity,
  onRemove,
}: {
  item: OrderItem;
  onUpdateQuantity: (menuItemId: string, quantity: number) => void;
  onRemove: (menuItemId: string) => void;
}) {
  const subtotal = item.unitPrice * item.quantity;

  return (
    <div className="cart-item-row">
      <div className="cart-item-info">
        <span className="cart-item-name">{item.name}</span>
        <span className="cart-item-price">
          ${item.unitPrice.toFixed(2)} each
        </span>
      </div>

      <div className="cart-item-controls">
        <button
          className="cart-qty-btn cart-qty-btn--minus"
          onClick={() =>
            item.quantity > 1
              ? onUpdateQuantity(item.menuItemId, item.quantity - 1)
              : onRemove(item.menuItemId)
          }
          aria-label={`Decrease quantity of ${item.name}`}
        >
          −
        </button>

        <span className="cart-qty-display" aria-live="polite">
          {item.quantity}
        </span>

        <button
          className="cart-qty-btn cart-qty-btn--plus"
          onClick={() => onUpdateQuantity(item.menuItemId, item.quantity + 1)}
          aria-label={`Increase quantity of ${item.name}`}
        >
          +
        </button>
      </div>

      <span className="cart-item-subtotal">${subtotal.toFixed(2)}</span>
    </div>
  );
}

/**
 * Renders the cart summary (totals, tax, etc.).
 */
function CartSummary({
  subtotal,
  taxRate,
  deliveryFee,
  totalAmount,
}: {
  subtotal: number;
  taxRate: number;
  deliveryFee: number;
  totalAmount: number;
}) {
  const taxAmount = subtotal * taxRate;

  return (
    <div className="cart-summary">
      <h3 className="cart-summary-title">Order Summary</h3>

      <div className="cart-summary-row">
        <span>Subtotal</span>
        <span>${subtotal.toFixed(2)}</span>
      </div>

      <div className="cart-summary-row">
        <span>Tax ({(taxRate * 100).toFixed(0)}%)</span>
        <span>${taxAmount.toFixed(2)}</span>
      </div>

      <div className="cart-summary-row">
        <span>Delivery Fee</span>
        <span>${deliveryFee.toFixed(2)}</span>
      </div>

      <div className="cart-summary-divider" />

      <div className="cart-summary-row cart-summary-row--total">
        <span>Total</span>
        <span>${totalAmount.toFixed(2)}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Cart component
// ---------------------------------------------------------------------------

interface CartProps {
  /** Current tax rate (e.g. 0.08 for 8%) */
  taxRate?: number;
  /** Delivery fee */
  deliveryFee?: number;
  /** Called when the user confirms the order; receives the final cart items */
  onCheckout?: (items: OrderItem[]) => void;
  /** Whether the cart panel is currently visible */
  isOpen?: boolean;
}

/**
 * Cart component that manages the customer's order.
 * Items are persisted to localStorage so they survive page refreshes.
 */
export default function Cart({
  taxRate = 0.08,
  deliveryFee = 0,
  onCheckout,
  isOpen = true,
}: CartProps) {
  const [cart, setCart] = useState<OrderItem[]>(loadCart);

  // Persist cart whenever it changes
  useEffect(() => {
    saveCart(cart);
  }, [cart]);

  // -----------------------------------------------------------------------
  // Handlers
  // -----------------------------------------------------------------------

  const addItem = useCallback(
    (menuItem: { id: string; name: string; price: number }) => {
      setCart((prev) => {
        const existing = prev.find((i) => i.menuItemId === menuItem.id);
        if (existing) {
          return prev.map((i) =>
            i.menuItemId === menuItem.id
              ? { ...i, quantity: i.quantity + 1 }
              : i
          );
        }
        return [
          ...prev,
          {
            menuItemId: menuItem.id,
            name: menuItem.name,
            quantity: 1,
            unitPrice: menuItem.price,
          },
        ];
      });
    },
    []
  );

  const updateQuantity = useCallback(
    (menuItemId: string, quantity: number) => {
      if (quantity < 1) return;
      setCart((prev) =>
        prev.map((i) =>
          i.menuItemId === menuItemId ? { ...i, quantity } : i
        )
      );
    },
    []
  );

  const removeItem = useCallback((menuItemId: string) => {
    setCart((prev) => prev.filter((i) => i.menuItemId !== menuItemId));
  }, []);

  const clearCart = useCallback(() => {
    setCart([]);
  }, []);

  // -----------------------------------------------------------------------
  // Derived values
  // -----------------------------------------------------------------------

  const subtotal = cart.reduce(
    (sum, item) => sum + item.unitPrice * item.quantity,
    0
  );
  const totalAmount = subtotal + subtotal * taxRate + deliveryFee;
  const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  if (!isOpen) return null;

  return (
    <div className="cart-panel" role="dialog" aria-label="Shopping cart">
      <div className="cart-header">
        <h2 className="cart-title">Your Cart</h2>
        {cart.length > 0 && (
          <button
            className="cart-clear-btn"
            onClick={clearCart}
            aria-label="Clear cart"
          >
            Clear
          </button>
        )}
      </div>

      {cart.length === 0 ? (
        <div className="cart-empty">
          <p>Your cart is empty.</p>
          <p className="cart-empty-hint">
            Browse the menu and tap + to add items.
          </p>
        </div>
      ) : (
        <>
          <div className="cart-items" role="list">
            {cart.map((item) => (
              <CartItemRow
                key={item.menuItemId}
                item={item}
                onUpdateQuantity={updateQuantity}
                onRemove={removeItem}
              />
            ))}
          </div>

          <CartSummary
            subtotal={subtotal}
            taxRate={taxRate}
            deliveryFee={deliveryFee}
            totalAmount={totalAmount}
          />

          <button
            className="cart-checkout-btn"
            onClick={() => onCheckout?.(cart)}
            disabled={cart.length === 0}
          >
            Checkout ({itemCount} item{itemCount !== 1 ? "s" : ""}) — $
            {totalAmount.toFixed(2)}
          </button>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Expose helpers for parent components (e.g. MenuBrowse) to call
// ---------------------------------------------------------------------------

export { loadCart, saveCart };
