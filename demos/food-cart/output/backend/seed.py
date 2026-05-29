from database import get_db, init_db

CATEGORIES = [
    ('Tacos', 1),
    ('Bowls', 2),
    ('Sides', 3),
    ('Drinks', 4),
]

ITEMS = [
    ('Carnitas Taco', 'Slow-braised pork, salsa verde, onion, cilantro.', 450, 1, 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?auto=format&fit=crop&w=900&q=80', 1, 1),
    ('Mushroom Taco', 'Roasted mushrooms, crema, pickled onion, cotija.', 425, 1, 'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=900&q=80', 1, 2),
    ('Chicken Tinga Taco', 'Smoky shredded chicken with avocado salsa.', 475, 1, 'https://images.unsplash.com/photo-1613514785940-daed07799d9b?auto=format&fit=crop&w=900&q=80', 1, 3),
    ('Street Corn Bowl', 'Rice, beans, charred corn, crema, lime, herbs.', 1150, 2, 'https://images.unsplash.com/photo-1543339308-43e59d6b73a6?auto=format&fit=crop&w=900&q=80', 1, 1),
    ('Barbacoa Bowl', 'Tender beef, rice, black beans, pico, queso fresco.', 1295, 2, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=80', 1, 2),
    ('Chips & Salsa', 'Crispy corn chips with roasted tomato salsa.', 500, 3, 'https://images.unsplash.com/photo-1626200419199-391ae4be7a41?auto=format&fit=crop&w=900&q=80', 1, 1),
    ('Guacamole Cup', 'Fresh avocado, lime, cilantro, jalapeño.', 650, 3, 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=900&q=80', 1, 2),
    ('Agua Fresca', 'Rotating seasonal fruit agua fresca over ice.', 400, 4, 'https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80', 1, 1),
    ('Mexican Coke', 'Classic glass bottle Coke made with cane sugar.', 350, 4, 'https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=900&q=80', 1, 2),
]

def seed_database():
    init_db()
    conn = get_db()
    if conn.execute('SELECT COUNT(*) AS c FROM categories').fetchone()['c'] == 0:
        conn.executemany('INSERT INTO categories (name, sort_order) VALUES (?, ?)', CATEGORIES)
    if conn.execute('SELECT COUNT(*) AS c FROM menu_items').fetchone()['c'] == 0:
        conn.executemany(
            '''INSERT INTO menu_items
               (name, description, price, category_id, photo_url, available, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            ITEMS
        )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_database()
    print('Seeded food cart database')
