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
  photo_url: string | null;
  is_available: boolean;
  sort_order: number;
}

export interface OrderItem {
  id: number;
  order_id: number;
  menu_item_id: number;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface Order {
  id: number;
  order_number: string;
  customer_name: string | null;
  customer_phone: string | null;
  status: string;
  subtotal: number;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface CartSettings {
  id: number;
  cart_name: string;
  opening_time: string;
  closing_time: string;
  admin_pin: string;
}

export interface DailySummary {
  date: string;
  order_count: number;
  total_sales: number;
}

export interface CreateCategoryInput {
  name: string;
  sort_order: number;
}

export interface UpdateCategoryInput {
  name: string;
  sort_order: number;
}

export interface CreateMenuItemInput {
  name: string;
  description: string;
  price: number;
  category_id: number;
  photo_url: string | null;
  is_available: boolean;
  sort_order: number;
}

export interface UpdateMenuItemInput {
  name: string;
  description: string;
  price: number;
  category_id: number;
  photo_url: string | null;
  is_available: boolean;
  sort_order: number;
}

export interface CreateOrderItemInput {
  menu_item_id: number;
  quantity: number;
}

export interface CreateOrderInput {
  customer_name: string | null;
  customer_phone: string | null;
  items: CreateOrderItemInput[];
}

export interface UpdateOrderStatusInput {
  status: string;
}

export interface UpdateSettingsInput {
  cart_name: string;
  opening_time: string;
  closing_time: string;
  admin_pin: string;
}
