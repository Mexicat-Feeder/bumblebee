from database import get_db, init_db


CATEGORIES = [
    ('Tacos', 1),
    ('Bowls', 2),
    ('Sides', 3),
    ('Drinks', 4),
]

ITEMS = [
    ('Al Pastor Taco', 'Marinated pork, pineapple, onion, cilantro.', 450, 1, 'https://images.unsplash.com/photo-1613514785940-daed07799d9b?auto=format&fit=crop&w=800&q=80', 1, 1),
    ('Carne Asada Taco', 'Grilled steak, salsa roja, onion, cilantro.', 500, 1, 'https://images.unsplash.com/photo-1565299585323-38174c4a6c8f?auto=format&fit=crop&w=800&q=80', 1, 2),
    ('Veggie Taco', 'Roasted peppers, black beans, avocado crema.', 425, 1, 'https://images.unsplash.com/photo-1604467715878-83e57e8bc129?auto=format&fit=crop&w=800&q=80', 1, 3),
    ('Chicken Rice Bowl', 'Citrus chicken, rice, pico, slaw.', 1195, 2, 'https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=800&q=80', 1, 1),
    ('Steak Burrito Bowl', 'Steak, rice, beans, salsa, crema.', 1295, 2, 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80', 1, 2),
    ('Loaded Nachos', 'Chips, queso, beans, jalapenos, salsa.', 995, 2, 'https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?auto=format&fit=crop&w=800&q=80', 1, 3),
    ('Chips & Salsa', 'House fried chips with roasted tomato salsa.', 395, 3, 'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=800&q=80', 1, 1),
    ('Street Corn Cup', 'Charred corn, cotija, lime, chili.', 550, 3, 'https://images.unsplash.com/photo-1603046891744-76e6300f7f1d?auto=format&fit=crop&w=800&q=80', 1, 2),
    ('Horchata', 'Sweet rice milk with cinnamon.', 350, 4, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=800&q=80', 1, 1),
    ('Agua Fresca', 'Fresh fruit cooler, rotating flavor.', 325, 4, 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=800&q=80', 1, 2),
]


def seed() -> None:
    init_db()
    conn = get_db()
    conn.execute('DELETE FROM order_items')
    conn.execute('DELETE FROM orders')
    conn.execute('DELETE FROM menu_items')
    conn.execute('DELETE FROM categories')
    conn.execute('DELETE FROM settings')
    conn.executemany(
        'INSERT INTO categories (name, sort_order) VALUES (?, ?)',
        CATEGORIES,
    )
    conn.executemany(
        '''
        INSERT INTO menu_items
        (name, description, price, category_id, photo_url, available, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        ITEMS,
    )
    conn.execute(
        '''
        INSERT INTO settings (id, cart_name, tagline, is_open, estimated_wait_minutes, admin_pin)
        VALUES (1, ?, ?, ?, ?, ?)
        ''',
        ('Sunset Tacos', 'Fresh tacos and bowls made to order.', 1, 12, '1234'),
    )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    seed()
    print('Database seeded')
