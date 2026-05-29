from pydantic import BaseModel
from typing import List, Literal

OrderStatus = Literal['received', 'in_progress', 'ready', 'picked_up']

class Category(BaseModel):
    id: int
    name: str
    sort_order: int

class CategoryInput(BaseModel):
    name: str
    sort_order: int = 0

class MenuItem(BaseModel):
    id: int
    name: str
    description: str
    price: int
    category_id: int
    category_name: str
    photo_url: str
    available: bool
    sort_order: int

class MenuItemInput(BaseModel):
    name: str
    description: str
    price: int
    category_id: int
    photo_url: str = ''
    available: bool = True
    sort_order: int = 0

class Settings(BaseModel):
    cart_name: str
    tagline: str
    is_open: bool
    estimated_wait_minutes: int
    admin_pin: str

class OrderItem(BaseModel):
    id: int
    order_id: int
    item_id: int
    item_name: str
    item_price: int
    quantity: int

class Order(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: OrderStatus
    created_at: str
    updated_at: str
    items: List[OrderItem]
    total: int

class CreateOrderItem(BaseModel):
    item_id: int
    quantity: int

class CreateOrderRequest(BaseModel):
    customer_name: str
    items: List[CreateOrderItem]

class UpdateOrderStatus(BaseModel):
    status: OrderStatus
