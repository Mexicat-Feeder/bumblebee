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
  category_id: number;
  category_name: string;
  photo_url: string;
  available: boolean;
  sort_order: number;
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
  items: OrderItem[];
}

export interface Settings {
  cart_name: string;
  tagline: string;
  is_open: boolean;
  estimated_wait_minutes: number;
  admin_pin: string;
}

export interface CartItem {
  item: MenuItem;
  quantity: number;
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

export interface CategoryInput {
  name: string;
  sort_order: number;
}

export interface MenuItemInput {
  name: string;
  description: string;
  price: number;
  category_id: number;
  photo_url: string;
  available: boolean;
  sort_order: number;
}

export interface SettingsInput {
  cart_name: string;
  tagline: string;
  is_open: boolean;
  estimated_wait_minutes: number;
  admin_pin: string;
}

export interface AdminAuthInput {
  pin: string;
}

export interface AdminAuthResponse {
  success: boolean;
}
