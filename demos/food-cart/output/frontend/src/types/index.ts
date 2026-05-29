export interface Category {
  id: number;
  name: string;
  sort_order: number;
}

export interface MenuItem {
  id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  photo_url: string;
  available: boolean;
  sort_order: number;
}

export interface Settings {
  cart_name: string;
  tagline: string;
  is_open: boolean;
  estimated_wait_minutes: number;
  admin_pin: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  item_id: number;
  item_name: string;
  item_price: number;
  quantity: number;
}

export interface Order {
  id: number;
  order_number: string;
  customer_name: string;
  status: string;
  created_at: string;
  updated_at: string;
  items?: OrderItem[];
}

export interface CreateOrderItemInput {
  item_id: number;
  quantity: number;
}

export interface CreateOrderInput {
  customer_name: string;
  items: CreateOrderItemInput[];
}

export interface UpdateOrderStatusInput {
  status: string;
}

export interface UpsertMenuItemInput {
  name: string;
  description: string;
  price: number;
  category: string;
  photo_url: string;
  available: boolean;
  sort_order: number;
}

export interface UpdateSettingsInput {
  cart_name: string;
  tagline: string;
  is_open: boolean;
  estimated_wait_minutes: number;
  admin_pin: string;
}
