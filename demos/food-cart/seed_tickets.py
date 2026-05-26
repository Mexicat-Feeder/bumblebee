"""Seed all Food Cart tickets into the Bumblebee DB."""
import sys, os, sqlite3, json
# Add bumblebee root to path so engine imports work
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BUMBLEBEE_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
sys.path.insert(0, _BUMBLEBEE_ROOT)  # for engine.* imports
sys.path.insert(0, os.path.dirname(_BUMBLEBEE_ROOT))  # for bumblebee.* imports

from engine.event_log import init_db

DB_PATH = os.path.join(os.path.dirname(__file__), 'tickets.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
init_db(conn)

TICKETS = [

# ═══════════════════════════════════════════════════════════════
# PHASE 1 — FOUNDATION
# ═══════════════════════════════════════════════════════════════

{
"id": "FC-P1-001",
"gate": 1,
"depends_on": [],
"output_files": [
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "frontend/tailwind.config.js",
    "frontend/postcss.config.js",
    "frontend/index.html",
    "frontend/src/index.css",
    "backend/requirements.txt",
],
"qa_cmd": ["cd frontend && npm install && npm run build"],
"description": r"""## Objective
Create the complete project skeleton — Vite+React+TypeScript frontend and FastAPI backend config files. No logic yet, just a project that builds clean.

## Files to write

### frontend/package.json
```json
{
  "name": "food-cart-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.2",
    "vite": "^5.4.9"
  }
}
```

### frontend/tsconfig.json
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

Also create `frontend/tsconfig.app.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

Also create `frontend/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true
  },
  "include": ["vite.config.ts"]
}
```

### frontend/vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
      '/uploads': 'http://localhost:8000',
    }
  }
})
```

### frontend/tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 500: '#f97316', 600: '#ea580c' }
      }
    }
  },
  plugins: []
}
```

### frontend/postcss.config.js
```javascript
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} }
}
```

### frontend/index.html
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Food Cart</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### frontend/src/index.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### backend/requirements.txt
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9
```

## QA
Run: `cd frontend && npm install && npm run build`
The build will fail if tsconfig is wrong or tailwind isn't configured. Fix any errors before finishing.
"""
},

{
"id": "FC-P1-002",
"gate": 1,
"depends_on": ["FC-P1-001"],
"output_files": [
    "frontend/src/types/index.ts",
    "backend/schemas.py",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Define shared TypeScript types (frontend) and Pydantic schemas (backend). These are the data contracts used by every other file in the project.

## Files to write

### frontend/src/types/index.ts
```typescript
export interface Category {
  id: number;
  name: string;
  sort_order: number;
}

export interface MenuItem {
  id: number;
  name: string;
  description: string;
  price: number;        // always in cents
  category_id: number;
  photo_url: string | null;
  available: boolean;
  sort_order: number;
}

export interface CartItem {
  item: MenuItem;
  quantity: number;
}

export interface OrderItem {
  id: number;
  item_name: string;
  item_price: number;   // cents
  quantity: number;
}

export interface Order {
  id: number;
  order_number: string; // e.g. "#001"
  customer_name: string;
  status: 'received' | 'in_progress' | 'ready';
  created_at: string;
  items: OrderItem[];
}

export interface Settings {
  cart_name: string;
  tagline: string;
  is_open: boolean;
  estimated_wait_minutes: number;
}
```

### backend/schemas.py
```python
from pydantic import BaseModel
from typing import Optional, List

class CategoryOut(BaseModel):
    id: int
    name: str
    sort_order: int

class MenuItemOut(BaseModel):
    id: int
    name: str
    description: str
    price: int          # cents
    category_id: int
    photo_url: Optional[str]
    available: bool
    sort_order: int

class OrderItemIn(BaseModel):
    item_id: int
    quantity: int

class OrderCreate(BaseModel):
    customer_name: str
    items: List[OrderItemIn]

class OrderItemOut(BaseModel):
    id: int
    item_name: str
    item_price: int     # cents
    quantity: int

class OrderOut(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: str
    created_at: str
    items: List[OrderItemOut]

class SettingsOut(BaseModel):
    cart_name: str
    tagline: str
    is_open: bool
    estimated_wait_minutes: int

class StatusUpdate(BaseModel):
    status: str
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P1-003",
"gate": 1,
"depends_on": ["FC-P1-001"],
"output_files": [
    "backend/database.py",
    "backend/seed.py",
],
"qa_cmd": ["cd backend && python seed.py && python -c \"import sqlite3; c=sqlite3.connect('food-cart.db'); print('items:', c.execute('SELECT COUNT(*) FROM menu_items').fetchone()[0])\""],
"description": r"""## Objective
Create the SQLite database module and seed script. Running `python seed.py` creates `food-cart.db` with tables, 3 categories, 10 menu items, and default settings.

## Files to write

### backend/database.py
```python
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'food-cart.db')

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price INTEGER NOT NULL,
            category_id INTEGER,
            photo_url TEXT,
            available INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            status TEXT DEFAULT 'received',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER,
            item_name TEXT NOT NULL,
            item_price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cart_name TEXT DEFAULT 'The Rolling Bite',
            tagline TEXT DEFAULT 'Fresh food, made fast',
            is_open INTEGER DEFAULT 1,
            estimated_wait_minutes INTEGER DEFAULT 10
        );
    ''')
    conn.commit()
    conn.close()
```

### backend/seed.py
```python
import sqlite3
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, get_db, DB_PATH

# Remove existing DB for fresh seed
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

init_db()
conn = get_db()

# Categories
cats = [
    (1, 'Mains', 1),
    (2, 'Sides', 2),
    (3, 'Drinks', 3),
]
conn.executemany("INSERT INTO categories (id, name, sort_order) VALUES (?, ?, ?)", cats)

# Menu items (price in cents)
items = [
    ('Smash Burger', 'Double smashed patty, American cheese, pickles, special sauce', 1200, 1, 1),
    ('Street Tacos (3)', 'Carne asada, white onion, cilantro, salsa verde', 1100, 1, 2),
    ('BBQ Pulled Pork Sandwich', 'Slow-cooked pulled pork, house slaw, pickles, brioche bun', 1300, 1, 3),
    ('Crispy Chicken Wrap', 'Fried chicken, shredded lettuce, ranch, flour tortilla', 1050, 1, 4),
    ('Veggie Bowl', 'Roasted seasonal vegetables, brown rice, tahini drizzle', 950, 1, 5),
    ('Loaded Fries', 'Crispy fries, cheddar, jalapeños, sour cream', 800, 2, 1),
    ('Onion Rings', 'Beer-battered, golden crisp, chipotle dipping sauce', 700, 2, 2),
    ('Side Salad', 'Mixed greens, cherry tomatoes, cucumber, balsamic vinaigrette', 600, 2, 3),
    ('Lemonade', 'Fresh-squeezed, sweetened, over ice', 400, 3, 1),
    ('Sparkling Water', 'Canned sparkling water, assorted flavors', 300, 3, 2),
]
conn.executemany(
    "INSERT INTO menu_items (name, description, price, category_id, sort_order) VALUES (?, ?, ?, ?, ?)",
    items
)

# Settings (id=1, always)
conn.execute('''
    INSERT OR REPLACE INTO settings (id, cart_name, tagline, is_open, estimated_wait_minutes)
    VALUES (1, 'The Rolling Bite', 'Fresh food, made fast', 1, 10)
''')

conn.commit()
conn.close()
print(f"Seeded: {len(cats)} categories, {len(items)} items")
print(f"DB: {DB_PATH}")
```

## QA
Run: `cd backend && python seed.py`
Should print item count. Then verify: `python -c "import sqlite3; c=sqlite3.connect('backend/food-cart.db'); print(c.execute('SELECT COUNT(*) FROM menu_items').fetchone())"`
"""
},

{
"id": "FC-P1-004",
"gate": 1,
"depends_on": ["FC-P1-001", "FC-P1-002"],
"output_files": [
    "frontend/src/components/ui/Button.tsx",
    "frontend/src/components/ui/Badge.tsx",
    "frontend/src/components/ui/Spinner.tsx",
    "frontend/src/components/ui/EmptyState.tsx",
    "frontend/src/components/Layout.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Create reusable UI primitives used across all pages. These components must be complete, not stubs.

## Context files to read
- `frontend/src/types/index.ts`

## Files to write

### frontend/src/components/ui/Button.tsx
```tsx
import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  children: React.ReactNode;
}

export default function Button({
  variant = 'primary', size = 'md', disabled, loading,
  onClick, type = 'button', className = '', children
}: ButtonProps) {
  const base = 'inline-flex items-center justify-center font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  const sizes = { sm: 'px-3 py-1.5 text-sm', md: 'px-4 py-2 text-base', lg: 'px-6 py-3 text-lg' };
  const variants = {
    primary: 'bg-orange-500 text-white hover:bg-orange-600 focus:ring-orange-500 disabled:bg-orange-300',
    secondary: 'border-2 border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-300',
    danger: 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500',
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
    >
      {loading ? <span className="mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" /> : null}
      {children}
    </button>
  );
}
```

### frontend/src/components/ui/Badge.tsx
```tsx
interface BadgeProps {
  status: 'received' | 'in_progress' | 'ready';
}

const LABELS = { received: 'Received', in_progress: 'In Progress', ready: 'Ready!' };
const COLORS = {
  received: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  ready: 'bg-green-100 text-green-800',
};

export default function Badge({ status }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${COLORS[status]}`}>
      {LABELS[status]}
    </span>
  );
}
```

### frontend/src/components/ui/Spinner.tsx
```tsx
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const SIZES = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' };

export default function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return (
    <div className={`${SIZES[size]} border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin ${className}`} />
  );
}
```

### frontend/src/components/ui/EmptyState.tsx
```tsx
import React from 'react';

interface EmptyStateProps {
  icon?: string;
  title: string;
  message?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon = '🍽️', title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      {message && <p className="text-gray-500 mb-6 max-w-sm">{message}</p>}
      {action}
    </div>
  );
}
```

### frontend/src/components/Layout.tsx
```tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface LayoutProps {
  title?: string;
  cartCount?: number;
  onCartClick?: () => void;
  showBack?: boolean;
  children: React.ReactNode;
}

export default function Layout({ title = 'The Rolling Bite', cartCount = 0, onCartClick, showBack, children }: LayoutProps) {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-orange-500 text-white sticky top-0 z-40 shadow-md">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {showBack && (
              <button onClick={() => navigate(-1)} className="text-white hover:text-orange-100 p-1">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <h1 className="text-lg font-bold">{title}</h1>
          </div>
          {onCartClick !== undefined && (
            <button onClick={onCartClick} className="relative p-2 hover:bg-orange-600 rounded-lg">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-white text-orange-600 text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </button>
          )}
        </div>
      </header>
      <main className="max-w-lg mx-auto px-4 py-4">
        {children}
      </main>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
Fix any TypeScript errors before finishing.
"""
},

# ═══════════════════════════════════════════════════════════════
# PHASE 2 — MENU & CART
# ═══════════════════════════════════════════════════════════════

{
"id": "FC-P2-001",
"gate": 2,
"depends_on": ["FC-P1-003"],
"output_files": [
    "backend/routers/__init__.py",
    "backend/routers/menu.py",
],
"qa_cmd": ["cd backend && python -c \"from routers.menu import router; print('menu router ok')\""],
"description": r"""## Objective
FastAPI router exposing all menu data endpoints.

## Context files to read
- `backend/database.py`
- `backend/schemas.py`

## Files to write

### backend/routers/__init__.py
Empty file.

### backend/routers/menu.py
```python
from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import MenuItemOut, CategoryOut
from typing import List

router = APIRouter()

@router.get("/api/menu", response_model=List[MenuItemOut])
def get_menu():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM menu_items WHERE available = 1 ORDER BY sort_order"
        ).fetchall()
        return [dict(r) | {"available": bool(r["available"])} for r in rows]
    finally:
        conn.close()

@router.get("/api/menu/{item_id}", response_model=MenuItemOut)
def get_menu_item(item_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        return dict(row) | {"available": bool(row["available"])}
    finally:
        conn.close()

@router.get("/api/categories", response_model=List[CategoryOut])
def get_categories():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
```

## QA
Run: `cd backend && python -c "from routers.menu import router; print('ok')"`
"""
},

{
"id": "FC-P2-002",
"gate": 2,
"depends_on": ["FC-P1-002", "FC-P1-004"],
"output_files": [
    "frontend/src/context/CartContext.tsx",
    "frontend/src/hooks/useCart.ts",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Global cart state via React Context. Persists to localStorage across page refresh.

## Context files to read
- `frontend/src/types/index.ts`

## Files to write

### frontend/src/context/CartContext.tsx
```tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { MenuItem, CartItem } from '../types';

interface CartContextValue {
  items: CartItem[];
  totalItems: number;
  totalCents: number;
  addItem: (item: MenuItem, quantity: number) => void;
  removeItem: (itemId: number) => void;
  updateQty: (itemId: number, quantity: number) => void;
  clearCart: () => void;
}

export const CartContext = createContext<CartContextValue>({
  items: [], totalItems: 0, totalCents: 0,
  addItem: () => {}, removeItem: () => {}, updateQty: () => {}, clearCart: () => {},
});

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(() => {
    try {
      const saved = localStorage.getItem('food-cart-items');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });

  useEffect(() => {
    localStorage.setItem('food-cart-items', JSON.stringify(items));
  }, [items]);

  const addItem = (item: MenuItem, quantity: number) => {
    setItems(prev => {
      const existing = prev.find(ci => ci.item.id === item.id);
      if (existing) {
        return prev.map(ci => ci.item.id === item.id
          ? { ...ci, quantity: ci.quantity + quantity } : ci);
      }
      return [...prev, { item, quantity }];
    });
  };

  const removeItem = (itemId: number) =>
    setItems(prev => prev.filter(ci => ci.item.id !== itemId));

  const updateQty = (itemId: number, quantity: number) => {
    if (quantity <= 0) { removeItem(itemId); return; }
    setItems(prev => prev.map(ci => ci.item.id === itemId ? { ...ci, quantity } : ci));
  };

  const clearCart = () => setItems([]);

  const totalItems = items.reduce((s, ci) => s + ci.quantity, 0);
  const totalCents = items.reduce((s, ci) => s + ci.item.price * ci.quantity, 0);

  return (
    <CartContext.Provider value={{ items, totalItems, totalCents, addItem, removeItem, updateQty, clearCart }}>
      {children}
    </CartContext.Provider>
  );
}
```

### frontend/src/hooks/useCart.ts
```typescript
import { useContext } from 'react';
import { CartContext } from '../context/CartContext';

export function useCart() {
  return useContext(CartContext);
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P2-003",
"gate": 2,
"depends_on": ["FC-P2-001", "FC-P2-002"],
"output_files": [
    "frontend/src/components/menu/CategoryTabs.tsx",
    "frontend/src/components/menu/ItemCard.tsx",
    "frontend/src/components/menu/MenuGrid.tsx",
    "frontend/src/pages/MenuPage.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Customer-facing menu browse page — category tabs, item cards, menu grid.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/hooks/useCart.ts`
- `frontend/src/components/Layout.tsx`

## Files to write

### frontend/src/components/menu/CategoryTabs.tsx
```tsx
import { Category } from '../../types';

interface Props {
  categories: Category[];
  activeId: number;
  onChange: (id: number) => void;
}

export default function CategoryTabs({ categories, activeId, onChange }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      <button
        onClick={() => onChange(0)}
        className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeId === 0 ? 'bg-orange-500 text-white' : 'bg-white text-gray-600 border border-gray-200'}`}
      >
        All
      </button>
      {categories.map(cat => (
        <button
          key={cat.id}
          onClick={() => onChange(cat.id)}
          className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeId === cat.id ? 'bg-orange-500 text-white' : 'bg-white text-gray-600 border border-gray-200'}`}
        >
          {cat.name}
        </button>
      ))}
    </div>
  );
}
```

### frontend/src/components/menu/ItemCard.tsx
```tsx
import { MenuItem } from '../../types';
import Button from '../ui/Button';

interface Props {
  item: MenuItem;
  onAdd: () => void;
}

export default function ItemCard({ item, onAdd }: Props) {
  const dollars = (item.price / 100).toFixed(2);
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {item.photo_url
        ? <img src={item.photo_url} alt={item.name} className="w-full h-40 object-cover" />
        : <div className="w-full h-40 bg-orange-50 flex items-center justify-center text-4xl">🍽️</div>
      }
      <div className="p-3">
        <div className="flex justify-between items-start mb-1">
          <h3 className="font-semibold text-gray-900 text-sm leading-tight">{item.name}</h3>
          <span className="text-orange-600 font-bold text-sm ml-2 flex-shrink-0">${dollars}</span>
        </div>
        <p className="text-gray-500 text-xs line-clamp-2 mb-3">{item.description}</p>
        <Button size="sm" onClick={onAdd} className="w-full">+ Add</Button>
      </div>
    </div>
  );
}
```

### frontend/src/components/menu/MenuGrid.tsx
```tsx
import { MenuItem } from '../../types';
import ItemCard from './ItemCard';

interface Props {
  items: MenuItem[];
  onAdd: (item: MenuItem) => void;
}

export default function MenuGrid({ items, onAdd }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {items.map(item => (
        <ItemCard key={item.id} item={item} onAdd={() => onAdd(item)} />
      ))}
    </div>
  );
}
```

### frontend/src/pages/MenuPage.tsx
```tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MenuItem, Category } from '../types';
import { useCart } from '../hooks/useCart';
import Layout from '../components/Layout';
import CategoryTabs from '../components/menu/CategoryTabs';
import MenuGrid from '../components/menu/MenuGrid';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';

export default function MenuPage() {
  const navigate = useNavigate();
  const { addItem, totalItems } = useCart();
  const [items, setItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeCategoryId, setActiveCategoryId] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/menu').then(r => r.json()),
      fetch('/api/categories').then(r => r.json()),
    ]).then(([menuItems, cats]) => {
      setItems(menuItems);
      setCategories(cats);
    }).finally(() => setLoading(false));
  }, []);

  const filtered = activeCategoryId === 0
    ? items
    : items.filter(i => i.category_id === activeCategoryId);

  return (
    <Layout
      cartCount={totalItems}
      onCartClick={() => navigate('/cart')}
    >
      <div className="space-y-4">
        <CategoryTabs
          categories={categories}
          activeId={activeCategoryId}
          onChange={setActiveCategoryId}
        />
        {loading
          ? <div className="flex justify-center py-16"><Spinner size="lg" /></div>
          : filtered.length === 0
            ? <EmptyState icon="🍽️" title="Nothing here yet" message="Check back soon!" />
            : <MenuGrid items={filtered} onAdd={(item) => addItem(item, 1)} />
        }
      </div>
    </Layout>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P2-004",
"gate": 2,
"depends_on": ["FC-P2-002", "FC-P2-003"],
"output_files": [
    "frontend/src/pages/ItemDetailPage.tsx",
    "frontend/src/pages/CartPage.tsx",
    "frontend/src/components/cart/CartItem.tsx",
    "frontend/src/components/cart/CartSummary.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Item detail view and cart review page.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/hooks/useCart.ts`
- `frontend/src/components/Layout.tsx`

## Files to write

### frontend/src/components/cart/CartItem.tsx
```tsx
import { CartItem as CartItemType } from '../../types';

interface Props {
  cartItem: CartItemType;
  onRemove: (id: number) => void;
  onUpdateQty: (id: number, qty: number) => void;
}

export default function CartItemRow({ cartItem, onRemove, onUpdateQty }: Props) {
  const { item, quantity } = cartItem;
  const subtotal = ((item.price * quantity) / 100).toFixed(2);
  return (
    <div className="flex items-center gap-3 bg-white rounded-xl p-3 border border-gray-100">
      {item.photo_url
        ? <img src={item.photo_url} alt={item.name} className="h-16 w-16 object-cover rounded-lg flex-shrink-0" />
        : <div className="h-16 w-16 bg-orange-50 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">🍽️</div>
      }
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-900 text-sm truncate">{item.name}</p>
        <p className="text-orange-600 font-bold text-sm">${subtotal}</p>
      </div>
      <div className="flex items-center gap-2">
        <button onClick={() => onUpdateQty(item.id, quantity - 1)}
          className="h-7 w-7 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-gray-200 font-bold">−</button>
        <span className="w-5 text-center text-sm font-semibold">{quantity}</span>
        <button onClick={() => onUpdateQty(item.id, quantity + 1)}
          className="h-7 w-7 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 hover:bg-orange-200 font-bold">+</button>
        <button onClick={() => onRemove(item.id)} className="ml-1 text-gray-400 hover:text-red-500">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
```

### frontend/src/components/cart/CartSummary.tsx
```tsx
interface Props { totalCents: number; }

export default function CartSummary({ totalCents }: Props) {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex justify-between items-center">
        <span className="text-gray-600 font-medium">Subtotal</span>
        <span className="text-gray-900 font-bold text-lg">${(totalCents / 100).toFixed(2)}</span>
      </div>
      <p className="text-xs text-gray-400 mt-1">Pay at the cart when your order is ready</p>
    </div>
  );
}
```

### frontend/src/pages/ItemDetailPage.tsx
```tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MenuItem } from '../types';
import { useCart } from '../hooks/useCart';
import Layout from '../components/Layout';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';

export default function ItemDetailPage() {
  const { itemId } = useParams<{ itemId: string }>();
  const navigate = useNavigate();
  const { addItem, totalItems } = useCart();
  const [item, setItem] = useState<MenuItem | null>(null);
  const [qty, setQty] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/menu/${itemId}`).then(r => r.json()).then(setItem).finally(() => setLoading(false));
  }, [itemId]);

  if (loading) return <Layout showBack><div className="flex justify-center py-16"><Spinner size="lg" /></div></Layout>;
  if (!item) return <Layout showBack><p className="text-center py-16 text-gray-500">Item not found.</p></Layout>;

  const dollars = (item.price / 100).toFixed(2);
  const subtotal = ((item.price * qty) / 100).toFixed(2);

  return (
    <Layout showBack cartCount={totalItems} onCartClick={() => navigate('/cart')}>
      {item.photo_url
        ? <img src={item.photo_url} alt={item.name} className="w-full h-56 object-cover rounded-xl mb-4" />
        : <div className="w-full h-56 bg-orange-50 rounded-xl flex items-center justify-center text-6xl mb-4">🍽️</div>
      }
      <h2 className="text-2xl font-bold text-gray-900 mb-1">{item.name}</h2>
      <p className="text-orange-600 font-bold text-xl mb-3">${dollars}</p>
      <p className="text-gray-600 mb-6">{item.description}</p>
      <div className="flex items-center justify-center gap-6 mb-6">
        <button onClick={() => setQty(q => Math.max(1, q - 1))}
          className="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center text-xl font-bold text-gray-600 hover:bg-gray-200">−</button>
        <span className="text-2xl font-bold w-8 text-center">{qty}</span>
        <button onClick={() => setQty(q => q + 1)}
          className="h-10 w-10 rounded-full bg-orange-100 flex items-center justify-center text-xl font-bold text-orange-600 hover:bg-orange-200">+</button>
      </div>
      <Button size="lg" className="w-full" onClick={() => { addItem(item, qty); navigate('/'); }}>
        Add {qty} to Cart — ${subtotal}
      </Button>
    </Layout>
  );
}
```

### frontend/src/pages/CartPage.tsx
```tsx
import { useNavigate } from 'react-router-dom';
import { useCart } from '../hooks/useCart';
import Layout from '../components/Layout';
import CartItemRow from '../components/cart/CartItem';
import CartSummary from '../components/cart/CartSummary';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';

export default function CartPage() {
  const navigate = useNavigate();
  const { items, totalItems, totalCents, removeItem, updateQty, clearCart } = useCart();

  return (
    <Layout title="Your Cart" showBack cartCount={totalItems} onCartClick={() => {}}>
      {items.length === 0
        ? <EmptyState icon="🛒" title="Your cart is empty" message="Add some items from the menu."
            action={<Button onClick={() => navigate('/')}>Browse Menu</Button>} />
        : (
          <div className="space-y-3">
            {items.map(ci => (
              <CartItemRow key={ci.item.id} cartItem={ci} onRemove={removeItem} onUpdateQty={updateQty} />
            ))}
            <CartSummary totalCents={totalCents} />
            <Button size="lg" className="w-full" onClick={() => navigate('/checkout')}>
              Checkout — ${(totalCents / 100).toFixed(2)}
            </Button>
            <button onClick={clearCart} className="w-full text-sm text-gray-400 hover:text-red-500 py-2">
              Clear cart
            </button>
          </div>
        )
      }
    </Layout>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P2-005",
"gate": 2,
"depends_on": ["FC-P2-001", "FC-P2-004"],
"output_files": [
    "frontend/src/pages/CheckoutPage.tsx",
    "frontend/src/lib/api.ts",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Checkout page (name entry + order summary + place order) and shared API client module.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/hooks/useCart.ts`
- `frontend/src/components/Layout.tsx`

## Files to write

### frontend/src/lib/api.ts
```typescript
import { MenuItem, Category, Order, Settings } from '../types';

const BASE = '/api';

export async function getMenu(): Promise<MenuItem[]> {
  const r = await fetch(`${BASE}/menu`);
  return r.json();
}

export async function getMenuItem(id: number): Promise<MenuItem> {
  const r = await fetch(`${BASE}/menu/${id}`);
  return r.json();
}

export async function getCategories(): Promise<Category[]> {
  const r = await fetch(`${BASE}/categories`);
  return r.json();
}

export async function createOrder(customerName: string, items: { item_id: number; quantity: number }[]): Promise<Order> {
  const r = await fetch(`${BASE}/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_name: customerName, items }),
  });
  if (!r.ok) throw new Error('Failed to place order');
  return r.json();
}

export async function getOrder(id: number): Promise<Order> {
  const r = await fetch(`${BASE}/orders/${id}`);
  return r.json();
}

export async function getSettings(): Promise<Settings> {
  const r = await fetch(`${BASE}/settings`);
  return r.json();
}

export async function updateSettings(s: Partial<Settings>): Promise<Settings> {
  const r = await fetch(`${BASE}/admin/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(s),
  });
  return r.json();
}

export async function updateOrderStatus(orderId: number, status: string): Promise<Order> {
  const r = await fetch(`${BASE}/admin/orders/${orderId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  return r.json();
}

export async function getAdminMenu(): Promise<MenuItem[]> {
  const r = await fetch(`${BASE}/admin/menu`);
  return r.json();
}

export async function getAdminCategories(): Promise<Category[]> {
  const r = await fetch(`${BASE}/admin/categories`);
  return r.json();
}

export async function toggleItemAvailability(id: number, available: boolean): Promise<void> {
  await fetch(`${BASE}/admin/menu/${id}/availability`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ available }),
  });
}

export async function deleteMenuItem(id: number): Promise<void> {
  await fetch(`${BASE}/admin/menu/${id}`, { method: 'DELETE' });
}

export async function getAdminOrders(): Promise<Order[]> {
  const r = await fetch(`${BASE}/admin/orders`);
  return r.json();
}
```

### frontend/src/pages/CheckoutPage.tsx
```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../hooks/useCart';
import { createOrder } from '../lib/api';
import Layout from '../components/Layout';
import Button from '../components/ui/Button';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { items, totalCents, clearCart } = useCart();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim().length < 2) { setError('Please enter your name (at least 2 characters)'); return; }
    setLoading(true);
    setError('');
    try {
      const orderItems = items.map(ci => ({ item_id: ci.item.id, quantity: ci.quantity }));
      const order = await createOrder(name.trim(), orderItems);
      clearCart();
      navigate(`/confirmation/${order.id}`);
    } catch {
      setError('Something went wrong. Please try again.');
      setLoading(false);
    }
  };

  return (
    <Layout title="Checkout" showBack>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Your name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. Alex"
            className="w-full border border-gray-300 rounded-xl px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-orange-400"
          />
          {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
        </div>
        <div className="bg-white rounded-xl p-4 border border-gray-100 space-y-2">
          <h3 className="font-semibold text-gray-800 mb-3">Order summary</h3>
          {items.map(ci => (
            <div key={ci.item.id} className="flex justify-between text-sm">
              <span className="text-gray-600">{ci.item.name} × {ci.quantity}</span>
              <span className="font-medium">${((ci.item.price * ci.quantity) / 100).toFixed(2)}</span>
            </div>
          ))}
          <div className="border-t pt-2 flex justify-between font-bold">
            <span>Total</span>
            <span className="text-orange-600">${(totalCents / 100).toFixed(2)}</span>
          </div>
        </div>
        <Button type="submit" size="lg" loading={loading} className="w-full">
          Place Order
        </Button>
      </form>
    </Layout>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

# ═══════════════════════════════════════════════════════════════
# PHASE 3 — ORDER FLOW & REAL-TIME
# ═══════════════════════════════════════════════════════════════

{
"id": "FC-P3-001",
"gate": 3,
"depends_on": ["FC-P1-001"],
"output_files": [
    "backend/websocket_manager.py",
],
"qa_cmd": ["cd backend && python -c \"from websocket_manager import manager; print('ws manager ok')\""],
"description": r"""## Objective
WebSocket connection manager. Standalone module — manages rooms for per-order status and admin dashboard.

## Files to write

### backend/websocket_manager.py
```python
from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, room: str) -> None:
        await ws.accept()
        self.active.setdefault(room, []).append(ws)

    def disconnect(self, ws: WebSocket, room: str) -> None:
        if room in self.active:
            self.active[room] = [c for c in self.active[room] if c is not ws]

    async def broadcast(self, room: str, data: dict) -> None:
        dead: List[WebSocket] = []
        for ws in self.active.get(room, []):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)

# Singleton — import this instance everywhere
manager = ConnectionManager()
```

Room naming conventions:
- `order:{order_id}` — customer status page for a specific order
- `admin` — admin orders dashboard

## QA
Run: `cd backend && python -c "from websocket_manager import manager; print('ok')"`
"""
},

{
"id": "FC-P3-002",
"gate": 3,
"depends_on": ["FC-P3-001", "FC-P1-003", "FC-P2-001"],
"output_files": [
    "backend/routers/orders.py",
],
"qa_cmd": ["cd backend && python -c \"from routers.orders import router; print('orders router ok')\""],
"description": r"""## Objective
FastAPI router for order creation, retrieval, status updates, and WebSocket endpoints.

## Context files to read
- `backend/database.py`
- `backend/schemas.py`
- `backend/websocket_manager.py`

## Files to write

### backend/routers/orders.py
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from database import get_db
from schemas import OrderCreate, OrderOut, StatusUpdate
from websocket_manager import manager
from typing import List
import asyncio

router = APIRouter()

def _build_order_dict(conn, order_row) -> dict:
    order = dict(order_row)
    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ?", (order['id'],)
    ).fetchall()
    order['items'] = [dict(i) for i in items]
    return order

@router.post("/api/orders", response_model=OrderOut)
async def create_order(body: OrderCreate):
    conn = get_db()
    try:
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        order_number = f"#{count + 1:03d}"
        cur = conn.execute(
            "INSERT INTO orders (order_number, customer_name, status) VALUES (?, ?, 'received')",
            (order_number, body.customer_name)
        )
        order_id = cur.lastrowid
        for oi in body.items:
            item = conn.execute("SELECT * FROM menu_items WHERE id = ?", (oi.item_id,)).fetchone()
            if item:
                conn.execute(
                    "INSERT INTO order_items (order_id, item_id, item_name, item_price, quantity) VALUES (?, ?, ?, ?, ?)",
                    (order_id, oi.item_id, item['name'], item['price'], oi.quantity)
                )
        conn.commit()
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        result = _build_order_dict(conn, order)
        asyncio.create_task(manager.broadcast("admin", {"type": "new_order", "order": result}))
        return result
    finally:
        conn.close()

@router.get("/api/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int):
    conn = get_db()
    try:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Order not found")
        return _build_order_dict(conn, order)
    finally:
        conn.close()

@router.get("/api/admin/orders", response_model=List[OrderOut])
def get_admin_orders():
    conn = get_db()
    try:
        orders = conn.execute(
            "SELECT * FROM orders WHERE status != 'complete' ORDER BY id DESC"
        ).fetchall()
        return [_build_order_dict(conn, o) for o in orders]
    finally:
        conn.close()

@router.patch("/api/admin/orders/{order_id}/status", response_model=OrderOut)
async def update_order_status(order_id: int, body: StatusUpdate):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (body.status, order_id)
        )
        conn.commit()
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        result = _build_order_dict(conn, order)
        asyncio.create_task(manager.broadcast(
            f"order:{order_id}", {"type": "status_update", "status": body.status}
        ))
        asyncio.create_task(manager.broadcast(
            "admin", {"type": "order_updated", "order_id": order_id, "status": body.status}
        ))
        return result
    finally:
        conn.close()

@router.websocket("/ws/order/{order_id}")
async def order_websocket(ws: WebSocket, order_id: int):
    await manager.connect(ws, f"order:{order_id}")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, f"order:{order_id}")

@router.websocket("/ws/admin")
async def admin_websocket(ws: WebSocket):
    await manager.connect(ws, "admin")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, "admin")
```

## QA
Run: `cd backend && python -c "from routers.orders import router; print('ok')"`
"""
},

{
"id": "FC-P3-003",
"gate": 3,
"depends_on": ["FC-P2-005", "FC-P1-004"],
"output_files": [
    "frontend/src/pages/ConfirmationPage.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Post-checkout confirmation screen: order number, items ordered, link to live status page.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/components/Layout.tsx`

## Files to write

### frontend/src/pages/ConfirmationPage.tsx
```tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Order } from '../types';
import { getOrder } from '../lib/api';
import Layout from '../components/Layout';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';

export default function ConfirmationPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orderId) {
      getOrder(parseInt(orderId)).then(setOrder).finally(() => setLoading(false));
    }
  }, [orderId]);

  if (loading) return <Layout><div className="flex justify-center py-16"><Spinner size="lg" /></div></Layout>;
  if (!order) return <Layout><p className="text-center py-16 text-gray-500">Order not found.</p></Layout>;

  return (
    <Layout title="Order Placed!">
      <div className="text-center space-y-4 py-6">
        <div className="text-6xl">✅</div>
        <h2 className="text-2xl font-bold text-gray-900">You're all set, {order.customer_name}!</h2>
        <p className="text-4xl font-bold text-orange-500">{order.order_number}</p>
        <p className="text-gray-500">We'll call your name when it's ready</p>
        <div className="bg-white rounded-xl p-4 border border-gray-100 text-left space-y-2">
          {order.items.map(oi => (
            <div key={oi.id} className="flex justify-between text-sm">
              <span className="text-gray-700">{oi.item_name} × {oi.quantity}</span>
              <span className="font-medium">${((oi.item_price * oi.quantity) / 100).toFixed(2)}</span>
            </div>
          ))}
        </div>
        <Button size="lg" className="w-full" onClick={() => navigate(`/order/${order.id}`)}>
          Track My Order
        </Button>
      </div>
    </Layout>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P3-004",
"gate": 3,
"depends_on": ["FC-P1-002"],
"output_files": [
    "frontend/src/hooks/useOrderWebSocket.ts",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
React hook that connects a customer to their order's WebSocket room and calls a handler on status updates.

## Files to write

### frontend/src/hooks/useOrderWebSocket.ts
```typescript
import { useEffect } from 'react';

export function useOrderWebSocket(
  orderId: string,
  onMessage: (data: { type: string; status?: string }) => void
): void {
  useEffect(() => {
    if (!orderId) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/order/${orderId}`);
    ws.onmessage = (e) => {
      try {
        onMessage(JSON.parse(e.data));
      } catch {}
    };
    ws.onerror = () => {};
    return () => { ws.close(); };
  }, [orderId]);
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P3-005",
"gate": 3,
"depends_on": ["FC-P3-004", "FC-P1-004"],
"output_files": [
    "frontend/src/pages/OrderStatusPage.tsx",
    "frontend/src/components/order/StatusTracker.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Live order status page. Shows 3-step tracker (Received → In Progress → Ready) that updates in real time via WebSocket.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/hooks/useOrderWebSocket.ts`
- `frontend/src/lib/api.ts`

## Files to write

### frontend/src/components/order/StatusTracker.tsx
```tsx
import { Order } from '../../types';

interface Props { status: Order['status']; }

const STEPS: { key: Order['status']; label: string; emoji: string }[] = [
  { key: 'received', label: 'Order Received', emoji: '📋' },
  { key: 'in_progress', label: 'In Progress', emoji: '👨‍🍳' },
  { key: 'ready', label: 'Ready!', emoji: '🎉' },
];

const ORDER: Record<Order['status'], number> = { received: 0, in_progress: 1, ready: 2 };

export default function StatusTracker({ status }: Props) {
  const currentIdx = ORDER[status] ?? 0;
  return (
    <div className="flex items-start justify-between relative">
      <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 mx-8" />
      {STEPS.map((step, idx) => {
        const done = idx <= currentIdx;
        return (
          <div key={step.key} className="flex flex-col items-center gap-2 z-10 flex-1">
            <div className={`h-10 w-10 rounded-full flex items-center justify-center text-lg border-2 transition-all ${done ? 'bg-green-500 border-green-500 text-white' : 'bg-white border-gray-200 text-gray-400'}`}>
              {step.emoji}
            </div>
            <span className={`text-xs font-medium text-center ${done ? 'text-green-700' : 'text-gray-400'}`}>
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
```

### frontend/src/pages/OrderStatusPage.tsx
```tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Order } from '../types';
import { getOrder } from '../lib/api';
import { useOrderWebSocket } from '../hooks/useOrderWebSocket';
import Layout from '../components/Layout';
import StatusTracker from '../components/order/StatusTracker';
import Spinner from '../components/ui/Spinner';

export default function OrderStatusPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orderId) {
      getOrder(parseInt(orderId)).then(setOrder).finally(() => setLoading(false));
    }
  }, [orderId]);

  useOrderWebSocket(orderId ?? '', (data) => {
    if (data.type === 'status_update' && data.status) {
      setOrder(prev => prev ? { ...prev, status: data.status as Order['status'] } : prev);
    }
  });

  if (loading) return <Layout><div className="flex justify-center py-16"><Spinner size="lg" /></div></Layout>;
  if (!order) return <Layout><p className="text-center py-16 text-gray-500">Order not found.</p></Layout>;

  return (
    <Layout title="Order Status">
      <div className="space-y-6 py-4">
        <div className="text-center">
          <p className="text-5xl font-bold text-orange-500 mb-1">{order.order_number}</p>
          <p className="text-gray-500">for {order.customer_name}</p>
        </div>
        <StatusTracker status={order.status} />
        {order.status === 'ready' && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
            <div className="text-4xl mb-2">🎉</div>
            <h3 className="text-xl font-bold text-green-800">Your order is ready!</h3>
            <p className="text-green-600 mt-1">Come pick it up at the cart</p>
          </div>
        )}
        <div className="bg-white rounded-xl p-4 border border-gray-100">
          <h4 className="font-semibold text-gray-700 mb-2 text-sm">Your order</h4>
          {order.items.map(oi => (
            <div key={oi.id} className="flex justify-between text-sm py-1">
              <span className="text-gray-600">{oi.item_name} × {oi.quantity}</span>
              <span className="font-medium">${((oi.item_price * oi.quantity) / 100).toFixed(2)}</span>
            </div>
          ))}
        </div>
        <button onClick={() => navigate('/')} className="w-full text-sm text-gray-400 hover:text-gray-600 py-2">
          Back to menu
        </button>
      </div>
    </Layout>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

# ═══════════════════════════════════════════════════════════════
# PHASE 4 — ADMIN
# ═══════════════════════════════════════════════════════════════

{
"id": "FC-P4-001",
"gate": 4,
"depends_on": ["FC-P1-004", "FC-P1-002"],
"output_files": [
    "frontend/src/pages/admin/PinPage.tsx",
    "frontend/src/context/AdminAuthContext.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Admin PIN gate (hardcoded PIN: 1234) and session auth context. Auth state is session-only — refreshing the page requires re-entry.

## Context files to read
- `frontend/src/components/Layout.tsx`

## Files to write

### frontend/src/context/AdminAuthContext.tsx
```tsx
import React, { createContext, useContext, useState } from 'react';

const ADMIN_PIN = '1234';

interface AdminAuthContextValue {
  isAuthed: boolean;
  login: (pin: string) => boolean;
  logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextValue>({
  isAuthed: false, login: () => false, logout: () => {},
});

export function AdminAuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthed, setIsAuthed] = useState(false);
  const login = (pin: string): boolean => {
    if (pin === ADMIN_PIN) { setIsAuthed(true); return true; }
    return false;
  };
  const logout = () => setIsAuthed(false);
  return (
    <AdminAuthContext.Provider value={{ isAuthed, login, logout }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  return useContext(AdminAuthContext);
}
```

### frontend/src/pages/admin/PinPage.tsx
```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';

export default function PinPage() {
  const { login } = useAdminAuth();
  const navigate = useNavigate();
  const [pin, setPin] = useState('');
  const [error, setError] = useState(false);
  const [shake, setShake] = useState(false);

  const handleKey = (digit: string) => {
    const next = pin + digit;
    setPin(next);
    setError(false);
    if (next.length === 4) {
      if (login(next)) {
        navigate('/admin/orders');
      } else {
        setShake(true);
        setError(true);
        setTimeout(() => { setPin(''); setShake(false); }, 600);
      }
    }
  };

  const handleDelete = () => setPin(p => p.slice(0, -1));

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className={`bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm text-center ${shake ? 'animate-bounce' : ''}`}>
        <div className="text-3xl mb-2">🔐</div>
        <h1 className="text-xl font-bold text-gray-900 mb-1">Admin Access</h1>
        <p className="text-gray-500 text-sm mb-6">Enter your PIN</p>
        <div className="flex gap-3 justify-center mb-4">
          {[0, 1, 2, 3].map(i => (
            <div key={i} className={`h-4 w-4 rounded-full border-2 transition-colors ${i < pin.length ? 'bg-orange-500 border-orange-500' : 'border-gray-300'}`} />
          ))}
        </div>
        {error && <p className="text-red-500 text-sm mb-3">Incorrect PIN</p>}
        <div className="grid grid-cols-3 gap-3">
          {['1','2','3','4','5','6','7','8','9','','0','⌫'].map((k, i) => (
            <button
              key={i}
              disabled={!k}
              onClick={() => k === '⌫' ? handleDelete() : k ? handleKey(k) : undefined}
              className={`h-14 rounded-xl text-xl font-semibold transition-colors ${k ? 'bg-gray-100 hover:bg-gray-200 text-gray-900' : 'invisible'}`}
            >
              {k}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P4-002",
"gate": 4,
"depends_on": ["FC-P4-001"],
"output_files": [
    "frontend/src/pages/admin/AdminLayout.tsx",
    "frontend/src/components/admin/AdminNav.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Persistent admin shell layout with sidebar nav. Redirects to PIN page if not authenticated.

## Context files to read
- `frontend/src/context/AdminAuthContext.tsx`

## Files to write

### frontend/src/components/admin/AdminNav.tsx
```tsx
import { NavLink, useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';

const LINKS = [
  { to: '/admin/orders', label: 'Orders', emoji: '📋' },
  { to: '/admin/menu', label: 'Menu', emoji: '🍽️' },
  { to: '/admin/settings', label: 'Settings', emoji: '⚙️' },
];

export default function AdminNav() {
  const { logout } = useAdminAuth();
  const navigate = useNavigate();
  const handleLogout = () => { logout(); navigate('/admin'); };

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-48 bg-gray-900 min-h-screen p-4 gap-2">
        <div className="text-white font-bold text-lg mb-4 px-2">🍽️ Admin</div>
        {LINKS.map(link => (
          <NavLink key={link.to} to={link.to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? 'bg-orange-500 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`
            }>
            <span>{link.emoji}</span>{link.label}
          </NavLink>
        ))}
        <button onClick={handleLogout}
          className="mt-auto flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-white hover:bg-gray-800">
          🚪 Logout
        </button>
      </aside>
      {/* Mobile bottom bar */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex z-50">
        {LINKS.map(link => (
          <NavLink key={link.to} to={link.to} className={({ isActive }) =>
            `flex-1 flex flex-col items-center py-2 text-xs font-medium ${isActive ? 'text-orange-500' : 'text-gray-500'}`
          }>
            <span className="text-xl">{link.emoji}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </>
  );
}
```

### frontend/src/pages/admin/AdminLayout.tsx
```tsx
import { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../../context/AdminAuthContext';
import AdminNav from '../../components/admin/AdminNav';

export default function AdminLayout() {
  const { isAuthed } = useAdminAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthed) navigate('/admin');
  }, [isAuthed]);

  if (!isAuthed) return null;

  return (
    <div className="flex min-h-screen bg-gray-50">
      <AdminNav />
      <div className="flex-1 p-4 pb-20 md:pb-4 overflow-auto">
        <Outlet />
      </div>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P4-003",
"gate": 4,
"depends_on": ["FC-P4-002", "FC-P1-002"],
"output_files": [
    "frontend/src/pages/admin/OrdersDashboard.tsx",
    "frontend/src/components/admin/OrderCard.tsx",
    "frontend/src/hooks/useAdminWebSocket.ts",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Live admin orders dashboard. Fetches active orders on mount, receives new orders and status updates via WebSocket.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/components/ui/Badge.tsx`

## Files to write

### frontend/src/hooks/useAdminWebSocket.ts
```typescript
import { useEffect } from 'react';

export function useAdminWebSocket(onMessage: (data: any) => void): void {
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/admin`);
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)); } catch {}
    };
    ws.onerror = () => {};
    return () => { ws.close(); };
  }, []);
}
```

### frontend/src/components/admin/OrderCard.tsx
```tsx
import { Order } from '../../types';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

interface Props {
  order: Order;
  onStatusChange: (id: number, status: string) => void;
}

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr + 'Z').getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function OrderCard({ order, onStatusChange }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <div className="flex justify-between items-center">
        <div>
          <span className="text-xl font-bold text-orange-500">{order.order_number}</span>
          <span className="ml-2 font-semibold text-gray-800">{order.customer_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge status={order.status} />
          <span className="text-xs text-gray-400">{timeAgo(order.created_at)}</span>
        </div>
      </div>
      <div className="space-y-1">
        {order.items.map(oi => (
          <div key={oi.id} className="flex justify-between text-sm">
            <span className="text-gray-600">{oi.item_name} × {oi.quantity}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        {order.status === 'received' && (
          <Button size="sm" variant="secondary" onClick={() => onStatusChange(order.id, 'in_progress')}>
            👨‍🍳 In Progress
          </Button>
        )}
        {order.status === 'in_progress' && (
          <Button size="sm" onClick={() => onStatusChange(order.id, 'ready')}>
            ✅ Mark Ready
          </Button>
        )}
      </div>
    </div>
  );
}
```

### frontend/src/pages/admin/OrdersDashboard.tsx
```tsx
import { useState, useEffect } from 'react';
import { Order } from '../../types';
import { getAdminOrders, updateOrderStatus } from '../../lib/api';
import { useAdminWebSocket } from '../../hooks/useAdminWebSocket';
import OrderCard from '../../components/admin/OrderCard';
import EmptyState from '../../components/ui/EmptyState';
import Spinner from '../../components/ui/Spinner';

export default function OrdersDashboard() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAdminOrders().then(setOrders).finally(() => setLoading(false));
  }, []);

  useAdminWebSocket((data) => {
    if (data.type === 'new_order') {
      setOrders(prev => [data.order, ...prev]);
    } else if (data.type === 'order_updated') {
      setOrders(prev => prev.map(o =>
        o.id === data.order_id ? { ...o, status: data.status } : o
      ));
    }
  });

  const handleStatusChange = async (id: number, status: string) => {
    await updateOrderStatus(id, status);
    setOrders(prev => prev.map(o => o.id === id ? { ...o, status: status as Order['status'] } : o));
  };

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-3">
      <h2 className="text-xl font-bold text-gray-900">Live Orders</h2>
      {orders.length === 0
        ? <EmptyState icon="📋" title="No active orders" message="New orders will appear here in real time." />
        : orders.map(order => (
          <OrderCard key={order.id} order={order} onStatusChange={handleStatusChange} />
        ))
      }
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P4-004",
"gate": 4,
"depends_on": ["FC-P1-003", "FC-P3-002"],
"output_files": [
    "backend/routers/admin.py",
],
"qa_cmd": ["cd backend && python -c \"from routers.admin import router; print('admin router ok')\""],
"description": r"""## Objective
FastAPI router for admin operations — menu CRUD with file upload, category management.

## Context files to read
- `backend/database.py`
- `backend/schemas.py`

## Files to write

### backend/routers/admin.py

Implement all endpoints below. For file upload, use this EXACT pattern:

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from database import get_db
from schemas import MenuItemOut, CategoryOut, SettingsOut
from typing import Optional, List
import shutil, uuid, os

router = APIRouter()
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_photo(photo: UploadFile) -> Optional[str]:
    if not photo or not photo.filename:
        return None
    ext = photo.filename.rsplit('.', 1)[-1] if '.' in photo.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{ext}"
    dest = os.path.join(UPLOAD_DIR, filename)
    with open(dest, 'wb') as f:
        shutil.copyfileobj(photo.file, f)
    return f"/uploads/{filename}"

# Menu endpoints
@router.get("/api/admin/menu", response_model=List[MenuItemOut])
def admin_get_menu():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM menu_items ORDER BY sort_order").fetchall()
        return [dict(r) | {"available": bool(r["available"])} for r in rows]
    finally:
        conn.close()

@router.post("/api/admin/menu", response_model=MenuItemOut)
def admin_create_item(
    name: str = Form(...),
    description: str = Form(''),
    price: int = Form(...),
    category_id: int = Form(...),
    sort_order: int = Form(0),
    available: str = Form('1'),
    photo: Optional[UploadFile] = File(None),
):
    photo_url = _save_photo(photo) if photo and photo.filename else None
    avail = available not in ('0', 'false', 'False')
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO menu_items (name, description, price, category_id, sort_order, available, photo_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, description, price, category_id, sort_order, int(avail), photo_url)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM menu_items WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row) | {"available": bool(row["available"])}
    finally:
        conn.close()

@router.put("/api/admin/menu/{item_id}", response_model=MenuItemOut)
def admin_update_item(
    item_id: int,
    name: str = Form(...),
    description: str = Form(''),
    price: int = Form(...),
    category_id: int = Form(...),
    sort_order: int = Form(0),
    available: str = Form('1'),
    photo: Optional[UploadFile] = File(None),
):
    photo_url = _save_photo(photo) if photo and photo.filename else None
    avail = available not in ('0', 'false', 'False')
    conn = get_db()
    try:
        existing = conn.execute("SELECT photo_url FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Item not found")
        final_photo = photo_url if photo_url else existing["photo_url"]
        conn.execute(
            "UPDATE menu_items SET name=?, description=?, price=?, category_id=?, sort_order=?, available=?, photo_url=? WHERE id=?",
            (name, description, price, category_id, sort_order, int(avail), final_photo, item_id)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        return dict(row) | {"available": bool(row["available"])}
    finally:
        conn.close()

@router.delete("/api/admin/menu/{item_id}")
def admin_delete_item(item_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

@router.patch("/api/admin/menu/{item_id}/availability")
def admin_toggle_availability(item_id: int, body: dict):
    available = body.get("available", True)
    conn = get_db()
    try:
        conn.execute("UPDATE menu_items SET available = ? WHERE id = ?", (int(available), item_id))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()

# Category endpoints
@router.get("/api/admin/categories", response_model=List[CategoryOut])
def admin_get_categories():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@router.post("/api/admin/categories", response_model=CategoryOut)
def admin_create_category(body: dict):
    name = body.get("name", "")
    sort_order = body.get("sort_order", 0)
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO categories (name, sort_order) VALUES (?, ?)", (name, sort_order))
        conn.commit()
        row = conn.execute("SELECT * FROM categories WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)
    finally:
        conn.close()

# Settings endpoints
@router.get("/api/admin/settings", response_model=SettingsOut)
def admin_get_settings():
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return dict(row) | {"is_open": bool(row["is_open"])}
    finally:
        conn.close()

@router.put("/api/admin/settings", response_model=SettingsOut)
def admin_update_settings(body: dict):
    conn = get_db()
    try:
        conn.execute('''
            UPDATE settings SET
                cart_name = ?,
                tagline = ?,
                is_open = ?,
                estimated_wait_minutes = ?
            WHERE id = 1
        ''', (
            body.get("cart_name", "The Rolling Bite"),
            body.get("tagline", "Fresh food, made fast"),
            int(body.get("is_open", True)),
            body.get("estimated_wait_minutes", 10),
        ))
        conn.commit()
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return dict(row) | {"is_open": bool(row["is_open"])}
    finally:
        conn.close()
```

## QA
Run: `cd backend && python -c "from routers.admin import router; print('ok')"`
"""
},

{
"id": "FC-P4-005",
"gate": 4,
"depends_on": ["FC-P4-002", "FC-P4-004"],
"output_files": [
    "frontend/src/pages/admin/MenuManager.tsx",
    "frontend/src/components/admin/MenuItemRow.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Admin page listing all menu items with availability toggle, edit, and delete actions.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/lib/api.ts`

## Files to write

### frontend/src/components/admin/MenuItemRow.tsx
```tsx
import { MenuItem } from '../../types';
import Button from '../ui/Button';

interface Props {
  item: MenuItem;
  onToggle: (id: number, available: boolean) => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function MenuItemRow({ item, onToggle, onEdit, onDelete }: Props) {
  const dollars = (item.price / 100).toFixed(2);
  return (
    <div className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 p-3">
      {item.photo_url
        ? <img src={item.photo_url} alt={item.name} className="h-12 w-12 object-cover rounded-lg flex-shrink-0" />
        : <div className="h-12 w-12 bg-orange-50 rounded-lg flex items-center justify-center text-xl flex-shrink-0">🍽️</div>
      }
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-900 text-sm truncate">{item.name}</p>
        <p className="text-gray-500 text-xs">${dollars}</p>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onToggle(item.id, !item.available)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${item.available ? 'bg-green-500' : 'bg-gray-300'}`}
        >
          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${item.available ? 'translate-x-6' : 'translate-x-1'}`} />
        </button>
        <Button size="sm" variant="secondary" onClick={() => onEdit(item.id)}>Edit</Button>
        <Button size="sm" variant="danger" onClick={() => { if (confirm(`Delete ${item.name}?`)) onDelete(item.id); }}>Del</Button>
      </div>
    </div>
  );
}
```

### frontend/src/pages/admin/MenuManager.tsx
```tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MenuItem } from '../../types';
import { getAdminMenu, toggleItemAvailability, deleteMenuItem } from '../../lib/api';
import MenuItemRow from '../../components/admin/MenuItemRow';
import Button from '../../components/ui/Button';
import Spinner from '../../components/ui/Spinner';
import EmptyState from '../../components/ui/EmptyState';

export default function MenuManager() {
  const navigate = useNavigate();
  const [items, setItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAdminMenu().then(setItems).finally(() => setLoading(false));
  }, []);

  const handleToggle = async (id: number, available: boolean) => {
    await toggleItemAvailability(id, available);
    setItems(prev => prev.map(i => i.id === id ? { ...i, available } : i));
  };

  const handleDelete = async (id: number) => {
    await deleteMenuItem(id);
    setItems(prev => prev.filter(i => i.id !== id));
  };

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>;

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-900">Menu Items</h2>
        <Button size="sm" onClick={() => navigate('/admin/menu/new')}>+ Add Item</Button>
      </div>
      {items.length === 0
        ? <EmptyState icon="🍽️" title="No menu items" message="Add your first item."
            action={<Button onClick={() => navigate('/admin/menu/new')}>Add Item</Button>} />
        : items.map(item => (
          <MenuItemRow
            key={item.id} item={item}
            onToggle={handleToggle}
            onEdit={(id) => navigate(`/admin/menu/${id}/edit`)}
            onDelete={handleDelete}
          />
        ))
      }
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P4-006a",
"gate": 4,
"depends_on": ["FC-P1-004"],
"output_files": [
    "frontend/src/components/admin/ImageUpload.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Standalone photo upload UI component. Pure UI — no API calls, no FormData. File selection + live preview.

## Files to write

### frontend/src/components/admin/ImageUpload.tsx
```tsx
import { useRef, useState } from 'react';

interface Props {
  currentUrl: string | null;
  onChange: (file: File | null) => void;
}

export default function ImageUpload({ currentUrl, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const displayUrl = preview ?? currentUrl;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    if (file) {
      const objectUrl = URL.createObjectURL(file);
      setPreview(objectUrl);
      onChange(file);
    }
  };

  const handleRemove = () => {
    setPreview(null);
    onChange(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="space-y-2">
      <div className="w-full h-48 rounded-xl overflow-hidden border-2 border-dashed border-gray-300 bg-gray-50 flex items-center justify-center">
        {displayUrl
          ? <img src={displayUrl} alt="Preview" className="w-full h-full object-cover" />
          : <div className="text-center text-gray-400">
              <div className="text-4xl mb-2">📷</div>
              <p className="text-sm">No photo selected</p>
            </div>
        }
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex-1 border border-gray-300 rounded-lg py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          {displayUrl ? 'Change photo' : 'Choose photo'}
        </button>
        {displayUrl && (
          <button
            type="button"
            onClick={handleRemove}
            className="border border-red-200 rounded-lg px-3 py-2 text-sm text-red-500 hover:bg-red-50"
          >
            Remove
          </button>
        )}
      </div>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P4-006b",
"gate": 4,
"depends_on": ["FC-P4-006a", "FC-P4-004", "FC-P1-002"],
"output_files": [
    "frontend/src/pages/admin/ItemFormPage.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Add/edit item form. Uses ImageUpload component. Handles FormData submission with optional photo. Both add and edit modes.

## Context files to read
- `frontend/src/components/admin/ImageUpload.tsx`
- `frontend/src/types/index.ts`
- `frontend/src/lib/api.ts`

## Files to write

### frontend/src/pages/admin/ItemFormPage.tsx

Import ImageUpload exactly as:
```tsx
import ImageUpload from '../../components/admin/ImageUpload';
```

Full implementation:
```tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Category } from '../../types';
import { getAdminMenu, getAdminCategories } from '../../lib/api';
import ImageUpload from '../../components/admin/ImageUpload';
import Button from '../../components/ui/Button';
import Spinner from '../../components/ui/Spinner';
import Layout from '../../components/Layout';

interface FormState {
  name: string;
  description: string;
  price: string;       // dollars as string, e.g. "12.00"
  categoryId: string;
  sortOrder: string;
  available: boolean;
}

export default function ItemFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;
  const navigate = useNavigate();

  const [form, setForm] = useState<FormState>({
    name: '', description: '', price: '', categoryId: '', sortOrder: '0', available: true,
  });
  const [categories, setCategories] = useState<Category[]>([]);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [currentPhotoUrl, setCurrentPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getAdminCategories().then(setCategories);
    if (isEdit && id) {
      getAdminMenu().then(items => {
        const item = items.find(i => i.id === parseInt(id));
        if (item) {
          setForm({
            name: item.name,
            description: item.description,
            price: (item.price / 100).toFixed(2),
            categoryId: String(item.category_id),
            sortOrder: String(item.sort_order),
            available: item.available,
          });
          setCurrentPhotoUrl(item.photo_url);
        }
      }).finally(() => setLoading(false));
    }
  }, [id, isEdit]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const fd = new FormData();
    fd.append('name', form.name);
    fd.append('description', form.description);
    fd.append('price', String(Math.round(parseFloat(form.price) * 100)));
    fd.append('category_id', form.categoryId);
    fd.append('sort_order', form.sortOrder);
    fd.append('available', form.available ? '1' : '0');
    if (photoFile) fd.append('photo', photoFile);

    const url = isEdit ? `/api/admin/menu/${id}` : '/api/admin/menu';
    const method = isEdit ? 'PUT' : 'POST';
    // DO NOT set Content-Type header — browser sets multipart boundary automatically
    try {
      const r = await fetch(url, { method, body: fd });
      if (!r.ok) throw new Error('Save failed');
      navigate('/admin/menu');
    } catch {
      alert('Failed to save item. Please try again.');
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>;

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-bold text-gray-900 mb-4">{isEdit ? 'Edit Item' : 'Add Item'}</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Photo</label>
          <ImageUpload currentUrl={currentPhotoUrl} onChange={setPhotoFile} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Name *</label>
          <input required value={form.name} onChange={e => setForm(f => ({...f, name: e.target.value}))}
            className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Description</label>
          <textarea value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))}
            rows={3} className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Price ($) *</label>
            <input required type="number" step="0.01" min="0" value={form.price}
              onChange={e => setForm(f => ({...f, price: e.target.value}))}
              className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Category *</label>
            <select required value={form.categoryId} onChange={e => setForm(f => ({...f, categoryId: e.target.value}))}
              className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400">
              <option value="">Select...</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <input type="checkbox" id="available" checked={form.available}
            onChange={e => setForm(f => ({...f, available: e.target.checked}))}
            className="h-4 w-4 text-orange-500 rounded" />
          <label htmlFor="available" className="text-sm font-medium text-gray-700">Available to order</label>
        </div>
        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={submitting} className="flex-1">
            {isEdit ? 'Save Changes' : 'Add Item'}
          </Button>
          <Button type="button" variant="secondary" onClick={() => navigate('/admin/menu')}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

# ═══════════════════════════════════════════════════════════════
# PHASE 5 — SETTINGS & POLISH
# ═══════════════════════════════════════════════════════════════

{
"id": "FC-P5-001",
"gate": 5,
"depends_on": ["FC-P1-003"],
"output_files": [
    "backend/routers/settings.py",
],
"qa_cmd": ["cd backend && python -c \"from routers.settings import router; print('settings router ok')\""],
"description": r"""## Objective
FastAPI router for public settings endpoint (read cart name, open/closed status).

## Context files to read
- `backend/database.py`
- `backend/schemas.py`

## Files to write

### backend/routers/settings.py
```python
from fastapi import APIRouter
from database import get_db
from schemas import SettingsOut

router = APIRouter()

@router.get("/api/settings", response_model=SettingsOut)
def get_settings():
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        if not row:
            return {"cart_name": "The Rolling Bite", "tagline": "Fresh food, made fast",
                    "is_open": True, "estimated_wait_minutes": 10}
        return dict(row) | {"is_open": bool(row["is_open"])}
    finally:
        conn.close()
```

## QA
Run: `cd backend && python -c "from routers.settings import router; print('ok')"`
"""
},

{
"id": "FC-P5-002",
"gate": 5,
"depends_on": ["FC-P4-001", "FC-P5-001"],
"output_files": [
    "frontend/src/pages/admin/SettingsPage.tsx",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Admin settings form — cart name, tagline, estimated wait, open/closed toggle.

## Context files to read
- `frontend/src/types/index.ts`
- `frontend/src/lib/api.ts`

## Files to write

### frontend/src/pages/admin/SettingsPage.tsx
```tsx
import { useState, useEffect } from 'react';
import { Settings } from '../../types';
import { getSettings, updateSettings } from '../../lib/api';
import Button from '../../components/ui/Button';
import Spinner from '../../components/ui/Spinner';

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSettings().then(setSettings).finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateSettings(settings);
      setSettings(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  if (loading || !settings) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>;

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Cart Settings</h2>
      <form onSubmit={handleSave} className="space-y-4">
        <div className="bg-white rounded-xl border border-gray-100 p-4 space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Cart Name</label>
            <input value={settings.cart_name}
              onChange={e => setSettings(s => s ? {...s, cart_name: e.target.value} : s)}
              className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Tagline</label>
            <input value={settings.tagline}
              onChange={e => setSettings(s => s ? {...s, tagline: e.target.value} : s)}
              className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Estimated Wait (minutes)</label>
            <input type="number" min="1" value={settings.estimated_wait_minutes}
              onChange={e => setSettings(s => s ? {...s, estimated_wait_minutes: parseInt(e.target.value)} : s)}
              className="w-full border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>
        </div>
        <div className={`flex items-center justify-between p-4 rounded-xl border-2 ${settings.is_open ? 'border-green-300 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <div>
            <p className={`font-bold text-lg ${settings.is_open ? 'text-green-800' : 'text-red-700'}`}>
              {settings.is_open ? '🟢 Open for orders' : '🔴 Closed'}
            </p>
            <p className={`text-sm ${settings.is_open ? 'text-green-600' : 'text-red-500'}`}>
              {settings.is_open ? 'Customers can place orders' : 'Ordering is disabled'}
            </p>
          </div>
          <button type="button"
            onClick={() => setSettings(s => s ? {...s, is_open: !s.is_open} : s)}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${settings.is_open ? 'bg-green-500' : 'bg-gray-300'}`}>
            <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${settings.is_open ? 'translate-x-7' : 'translate-x-1'}`} />
          </button>
        </div>
        <Button type="submit" size="lg" loading={saving} className="w-full">
          {saved ? '✅ Saved!' : 'Save Settings'}
        </Button>
      </form>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

{
"id": "FC-P5-003",
"gate": 5,
"depends_on": ["FC-P1-004", "FC-P1-002"],
"output_files": [
    "frontend/src/components/ClosedBanner.tsx",
    "frontend/src/hooks/useSettings.ts",
],
"qa_cmd": ["cd frontend && npm run build"],
"description": r"""## Objective
Closed state hook and banner component. MenuPage and CheckoutPage use these to block ordering when the cart is closed.

## Context files to read
- `frontend/src/types/index.ts`

## Files to write

### frontend/src/hooks/useSettings.ts
```typescript
import { useState, useEffect } from 'react';
import { Settings } from '../types';

export function useSettings(): Settings | null {
  const [settings, setSettings] = useState<Settings | null>(null);
  useEffect(() => {
    fetch('/api/settings').then(r => r.json()).then(setSettings).catch(() => {});
  }, []);
  return settings;
}
```

### frontend/src/components/ClosedBanner.tsx
```tsx
interface Props {
  cartName: string;
  tagline: string;
}

export default function ClosedBanner({ cartName, tagline }: Props) {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="text-center space-y-4">
        <div className="text-6xl">🔴</div>
        <h1 className="text-3xl font-bold text-white">{cartName}</h1>
        <p className="text-xl text-gray-300">{tagline}</p>
        <div className="bg-gray-800 rounded-xl px-6 py-4 inline-block">
          <p className="text-gray-400 text-lg">We're closed right now</p>
          <p className="text-gray-500 text-sm mt-1">Check back soon!</p>
        </div>
      </div>
    </div>
  );
}
```

## QA
Run: `cd frontend && npm run build`
"""
},

]  # end TICKETS

# ─── Insert tickets ───────────────────────────────────────────

for t in TICKETS:
    conn.execute("""
        INSERT INTO tickets (id, status, gate, depends_on, owner, attempt_count, metadata_json)
        VALUES (?, 'todo', ?, ?, 'default', 0, '{}')
    """, (
        t["id"],
        t["gate"],
        ",".join(t["depends_on"]) if t["depends_on"] else "",
    ))
    conn.execute("""
        INSERT INTO ticket_requirements
            (ticket_id, ticket_description, qa_cmd_json, context_files_json, required_output_files_json)
        VALUES (?, ?, ?, ?, ?)
    """, (
        t["id"],
        t["description"],
        json.dumps(t.get("qa_cmd", [])),
        json.dumps([]),
        json.dumps(t["output_files"]),
    ))

conn.commit()

print(f"Seeded {len(TICKETS)} tickets into {DB_PATH}")
for g in sorted(set(t["gate"] for t in TICKETS)):
    phase_tickets = [t for t in TICKETS if t["gate"] == g]
    print(f"  Phase {g}: {len(phase_tickets)} tickets — {', '.join(t['id'] for t in phase_tickets)}")
