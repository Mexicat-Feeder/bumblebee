/**
 * OrderSubmit - Order submission form and confirmation page.
 * Allows customers to review their cart, enter customer details,
 * submit the order, and view a confirmation with the order number.
 */

import { useState, useEffect, useCallback } from "react";
import { OrderItem } from "../types/shared";
import '../styles/design-tokens.css';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface OrderSubmitPayload {
  customer_name: string;
  customer_phone?: string;
  customer_email?: string;
  order_type: "dine-in" | "takeaway" | "delivery";
  notes?: string;
  items: Array<{
    menu_item_id: string;
    quantity: number;
    unit_price: number;
  }>;
}

interface OrderConfirmation {
  orderNumber: string;
  customerName: string;
  orderType: string;
  totalAmount: number;
  estimatedTime: string;
  items: Array<{ name: string; quantity: number; unitPrice: number }>;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const CART_STORAGE_KEY = "bumblebee-cart";
const TAX_RATE = 0.08; // 8% tax

function loadCart(): OrderItem[] {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function clearCart(): void {
  try {
    localStorage.removeItem(CART_STORAGE_KEY);
  } catch {
    // ignore
  }
}

function calculateSubtotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);
}

function calculateTax(subtotal: number): number {
  return subtotal * TAX_RATE;
}

function calculateTotal(subtotal: number): number {
  return subtotal + calculateTax(subtotal);
}

function formatCurrency(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/**
 * Renders the order summary / review section.
 */
function OrderReview({
  items,
  subtotal,
  tax,
  total,
}: {
  items: OrderItem[];
  subtotal: number;
  tax: number;
  total: number;
}) {
  return (
    <div className="order-review">
      <h2 className="order-review__title">Order Review</h2>

      <div className="order-review__items">
        {items.map((item) => (
          <div key={item.menuItemId} className="order-review-item">
            <div className="order-review-item__info">
              <span className="order-review-item__name">{item.name}</span>
              <span className="order-review-item__qty">
                × {item.quantity}
              </span>
            </div>
            <span className="order-review-item__price">
              {formatCurrency(item.unitPrice * item.quantity)}
            </span>
          </div>
        ))}
      </div>

      <div className="order-review__totals">
        <div className="order-review__row">
          <span>Subtotal</span>
          <span>{formatCurrency(subtotal)}</span>
        </div>
        <div className="order-review__row">
          <span>Tax (8%)</span>
          <span>{formatCurrency(tax)}</span>
        </div>
        <div className="order-review__row order-review__row--total">
          <span>Total</span>
          <span>{formatCurrency(total)}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Renders the customer information form.
 */
function CustomerForm({
  values,
  onChange,
  errors,
}: {
  values: {
    customerName: string;
    customerPhone: string;
    customerEmail: string;
    orderType: "dine-in" | "takeaway" | "delivery";
    notes: string;
  };
  onChange: (field: string, value: string) => void;
  errors: Record<string, string>;
}) {
  return (
    <div className="customer-form">
      <h2 className="customer-form__title">Your Details</h2>

      <div className="form-group">
        <label htmlFor="customerName" className="form-label">
          Name <span className="form-required">*</span>
        </label>
        <input
          id="customerName"
          type="text"
          className={`form-input ${errors.customerName ? "form-input--error" : ""}`}
          placeholder="Your full name"
          value={values.customerName}
          onChange={(e) => onChange("customerName", e.target.value)}
          required
        />
        {errors.customerName && (
          <span className="form-error">{errors.customerName}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="customerPhone" className="form-label">
          Phone
        </label>
        <input
          id="customerPhone"
          type="tel"
          className="form-input"
          placeholder="Your phone number"
          value={values.customerPhone}
          onChange={(e) => onChange("customerPhone", e.target.value)}
        />
      </div>

      <div className="form-group">
        <label htmlFor="customerEmail" className="form-label">
          Email
        </label>
        <input
          id="customerEmail"
          type="email"
          className="form-input"
          placeholder="Your email address"
          value={values.customerEmail}
          onChange={(e) => onChange("customerEmail", e.target.value)}
        />
      </div>

      <div className="form-group">
        <label className="form-label">Order Type</label>
        <div className="order-type-selector">
          {(["dine-in", "takeaway", "delivery"] as const).map((type) => (
            <button
              key={type}
              type="button"
              className={`order-type-btn ${
                values.orderType === type
                  ? "order-type-btn--active"
                  : ""
              }`}
              onClick={() => onChange("orderType", type)}
            >
              {type === "dine-in"
                ? "🍽️ Dine-in"
                : type === "takeaway"
                ? "🥡 Takeaway"
                : "🚗 Delivery"}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="notes" className="form-label">
          Special Instructions
        </label>
        <textarea
          id="notes"
          className="form-textarea"
          placeholder="Any allergies or special requests?"
          rows={3}
          value={values.notes}
          onChange={(e) => onChange("notes", e.target.value)}
        />
      </div>
    </div>
  );
}

/**
 * Renders the order confirmation / success page.
 */
function OrderConfirmationPage({
  confirmation,
  onNewOrder,
}: {
  confirmation: OrderConfirmation;
  onNewOrder: () => void;
}) {
  return (
    <div className="order-confirmation">
      <div className="order-confirmation__icon">✓</div>
      <h2 className="order-confirmation__title">Order Confirmed!</h2>
      <p className="order-confirmation__subtitle">
        Your order has been placed successfully.
      </p>

      <div className="order-confirmation__details">
        <div className="order-confirmation__detail-row">
          <span className="order-confirmation__detail-label">
            Order Number
          </span>
          <span className="order-confirmation__detail-value">
            {confirmation.orderNumber}
          </span>
        </div>
        <div className="order-confirmation__detail-row">
          <span className="order-confirmation__detail-label">
            Order Type
          </span>
          <span className="order-confirmation__detail-value">
            {confirmation.orderType}
          </span>
        </div>
        <div className="order-confirmation__detail-row">
          <span className="order-confirmation__detail-label">
            Customer
          </span>
          <span className="order-confirmation__detail-value">
            {confirmation.customerName}
          </span>
        </div>
        <div className="order-confirmation__detail-row">
          <span className="order-confirmation__detail-label">
            Estimated Time
          </span>
          <span className="order-confirmation__detail-value">
            {confirmation.estimatedTime}
          </span>
        </div>
        <div className="order-confirmation__detail-row order-confirmation__detail-row--total">
          <span className="order-confirmation__detail-label">Total</span>
          <span className="order-confirmation__detail-value">
            {formatCurrency(confirmation.totalAmount)}
          </span>
        </div>
      </div>

      <div className="order-confirmation__items">
        <h3 className="order-confirmation__items-title">Order Summary</h3>
        {confirmation.items.map((item) => (
          <div key={item.name} className="order-confirmation-item">
            <span className="order-confirmation-item__name">
              {item.name}
            </span>
            <span className="order-confirmation-item__qty">
              × {item.quantity}
            </span>
            <span className="order-confirmation-item__price">
              {formatCurrency(item.unitPrice * item.quantity)}
            </span>
          </div>
        ))}
      </div>

      <button className="btn btn--primary btn--full" onClick={onNewOrder}>
        Place New Order
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function OrderSubmit() {
  const [cartItems, setCartItems] = useState<OrderItem[]>([]);
  const [step, setStep] = useState<"review" | "details" | "submitting" | "confirmed">("review");
  const [confirmation, setConfirmation] = useState<OrderConfirmation | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Form state
  const [formValues, setFormValues] = useState({
    customerName: "",
    customerPhone: "",
    customerEmail: "",
    orderType: "takeaway" as "dine-in" | "takeaway" | "delivery",
    notes: "",
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Load cart on mount
  useEffect(() => {
    const items = loadCart();
    if (items.length === 0) {
      // Redirect or show empty state — for now just show review with empty
    }
    setCartItems(items);
  }, []);

  const subtotal = calculateSubtotal(cartItems);
  const tax = calculateTax(subtotal);
  const total = calculateTotal(subtotal);

  const handleFormChange = useCallback((field: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user types
    setFormErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  const validateForm = useCallback((): boolean => {
    const errors: Record<string, string> = {};

    if (!formValues.customerName.trim()) {
      errors.customerName = "Name is required";
    }

    if (formValues.customerEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formValues.customerEmail)) {
      errors.customerEmail = "Please enter a valid email";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formValues]);

  const handleSubmit = useCallback(async () => {
    if (!validateForm()) return;

    setStep("submitting");
    setSubmitError(null);

    const payload: OrderSubmitPayload = {
      customer_name: formValues.customerName.trim(),
      customer_phone: formValues.customerPhone.trim() || undefined,
      customer_email: formValues.customerEmail.trim() || undefined,
      order_type: formValues.orderType,
      notes: formValues.notes.trim() || undefined,
      items: cartItems.map((item) => ({
        menu_item_id: item.menuItemId,
        quantity: item.quantity,
        unit_price: item.unitPrice,
      })),
    };

    try {
      const response = await fetch("/api/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || `Server error: ${response.status}`
        );
      }

      const data = await response.json();

      // Generate confirmation
      const orderNumber = data.order_number || `ORD-${Date.now().toString(36).toUpperCase()}`;
      const estimatedTime =
        formValues.orderType === "dine-in"
          ? "15–20 minutes"
          : formValues.orderType === "delivery"
          ? "25–35 minutes"
          : "10–15 minutes";

      setConfirmation({
        orderNumber,
        customerName: formValues.customerName.trim(),
        orderType: formValues.orderType,
        totalAmount: data.total_amount ?? total,
        estimatedTime,
        items: cartItems.map((item) => ({
          name: item.name,
          quantity: item.quantity,
          unitPrice: item.unitPrice,
        })),
      });

      clearCart();
      setStep("confirmed");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to submit order. Please try again.");
      setStep("details");
    }
  }, [cartItems, formValues, total, validateForm]);

  const handleNewOrder = useCallback(() => {
    setStep("review");
    setConfirmation(null);
    setSubmitError(null);
    setFormValues({
      customerName: "",
      customerPhone: "",
      customerEmail: "",
      orderType: "takeaway",
      notes: "",
    });
    setFormErrors({});
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="order-submit">
      {/* Header */}
      <header className="order-submit__header">
        <h1 className="order-submit__title">
          {step === "confirmed"
            ? "Order Confirmed"
            : step === "submitting"
            ? "Submitting Order..."
            : "Submit Order"}
        </h1>
      </header>

      {/* Progress Steps */}
      {step !== "confirmed" && step !== "submitting" && (
        <div className="order-submit__steps">
          <div
            className={`order-step ${
              step === "review" ? "order-step--active" : "order-step--complete"
            }`}
          >
            <span className="order-step__number">1</span>
            <span className="order-step__label">Review</span>
          </div>
          <div className="order-step__connector" />
          <div
            className={`order-step ${
              step === "details" ? "order-step--active" : "order-step--pending"
            }`}
          >
            <span className="order-step__number">2</span>
            <span className="order-step__label">Details</span>
          </div>
          <div className="order-step__connector" />
          <div
            className={`order-step ${
              step === "confirmed" ? "order-step--active" : "order-step--pending"
            }`}
          >
            <span className="order-step__number">3</span>
            <span className="order-step__label">Confirmation</span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {submitError && (
        <div className="order-submit__error" role="alert">
          <span className="order-submit__error-icon">⚠</span>
          <span>{submitError}</span>
        </div>
      )}

      {/* Content */}
      <main className="order-submit__content">
        {step === "review" && (
          <div className="order-submit__review-section">
            <OrderReview
              items={cartItems}
              subtotal={subtotal}
              tax={tax}
              total={total}
            />

            {cartItems.length === 0 ? (
              <div className="order-submit__empty">
                <p>Your cart is empty.</p>
                <button
                  className="btn btn--primary"
                  onClick={() => window.history.back()}
                >
                  Browse Menu
                </button>
              </div>
            ) : (
              <button
                className="btn btn--primary btn--full"
                onClick={() => setStep("details")}
              >
                Continue to Details
              </button>
            )}
          </div>
        )}

        {step === "details" && (
          <div className="order-submit__details-section">
            <CustomerForm
              values={formValues}
              onChange={handleFormChange}
              errors={formErrors}
            />

            <div className="order-submit__actions">
              <button
                className="btn btn--secondary"
                onClick={() => setStep("review")}
              >
                ← Back to Review
              </button>
              <button
                className="btn btn--primary"
                onClick={handleSubmit}
              >
                Place Order — {formatCurrency(total)}
              </button>
            </div>
          </div>
        )}

        {step === "submitting" && (
          <div className="order-submit__loading">
            <div className="spinner" />
            <p>Submitting your order...</p>
          </div>
        )}

        {step === "confirmed" && confirmation && (
          <OrderConfirmationPage
            confirmation={confirmation}
            onNewOrder={handleNewOrder}
          />
        )}
      </main>
    </div>
  );
}
