from typing import List
from pydantic import BaseModel


class Category(BaseModel):
    id: int
    name: str
    sort_order: int


class CategoryInput(BaseModel):
    name: str
    sort_order: int


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
    photo_url: str
    available: bool
    sort_order: int


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
    status: str
    created_at: str
    updated_at: str
    items: List[OrderItem]


class CreateOrderItemInput(BaseModel):
    item_id: int
    quantity: int


class CreateOrderInput(BaseModel):
    customer_name: str
    items: List[CreateOrderItemInput]


class UpdateOrderStatusInput(BaseModel):
    status: str


class Settings(BaseModel):
    cart_name: str
    tagline: str
    is_open: bool
    estimated_wait_minutes: int
    admin_pin: str


class SettingsInput(BaseModel):
    cart_name: str
    tagline: str
    is_open: bool
    estimated_wait_minutes: int
    admin_pin: str


class AdminAuthInput(BaseModel):
    pin: str


class AdminAuthResponse(BaseModel):
    success: bool
