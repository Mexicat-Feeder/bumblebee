/**
 * Shared TypeScript types for the Bumblebee Food Cart application.
 * Used across both frontend and backend modules.
 */

/**
 * Represents a menu category (e.g., "Burgers", "Drinks", "Sides").
 */
export interface MenuCategory {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  sortOrder: number;
}

/**
 * Represents a single menu item available for ordering.
 */
export interface MenuItem {
  id: string;
  categoryId: string;
  name: string;
  description?: string;
  price: number;
  image?: string;
  isAvailable: boolean;
  tags?: string[];
  allergens?: string[];
}

/**
 * Status of an order in its lifecycle.
 */
export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'ready'
  | 'delivered'
  | 'cancelled';

/**
 * Represents a single line item within an order.
 */
export interface OrderItem {
  menuItemId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  specialInstructions?: string;
}

/**
 * Represents a complete customer order.
 */
export interface Order {
  id: string;
  items: OrderItem[];
  status: OrderStatus;
  createdAt: string; // ISO 8601 timestamp
  updatedAt: string; // ISO 8601 timestamp
  customerName?: string;
  customerPhone?: string;
  totalAmount: number;
  notes?: string;
}

/**
 * Application settings that can be configured by the operator.
 */
export interface Settings {
  appName: string;
  currency: string;
  taxRate: number;
  deliveryFee: number;
  minOrderAmount: number;
  isOnline: boolean;
  businessName: string;
  businessAddress?: string;
  businessPhone?: string;
  businessEmail?: string;
  operatingHours?: {
    open: string;
    close: string;
  };
}
