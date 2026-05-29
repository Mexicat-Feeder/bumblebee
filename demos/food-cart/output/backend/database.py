import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), 'foodcart.db')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')

SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS menu_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  price INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  photo_url TEXT NOT NULL DEFAULT '',
  available INTEGER NOT NULL DEFAULT 1,
  sort_order INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(category_id) REFERENCES categories(id)
);
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_number TEXT NOT NULL UNIQUE,
  customer_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'received',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  item_name TEXT NOT NULL,
  item_price INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id)
);
CREATE TABLE IF NOT EXISTS settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  cart_name TEXT NOT NULL,
  tagline TEXT NOT NULL,
  is_open INTEGER NOT NULL,
  estimated_wait_minutes INTEGER NOT NULL,
  admin_pin TEXT NOT NULL
);
'''

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        '''INSERT OR IGNORE INTO settings
           (id, cart_name, tagline, is_open, estimated_wait_minutes, admin_pin)
           VALUES (1, 'Sunny Side Food Cart', 'Fresh street eats made with love', 1, 12, '1234')'''
    )
    conn.commit()
    conn.close()
