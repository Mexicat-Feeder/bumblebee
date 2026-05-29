from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import MenuItemInput

router = APIRouter(prefix='/api/items', tags=['items'])

def row_to_item(row):
    return {
        'id': row['id'], 'name': row['name'], 'description': row['description'],
        'price': row['price'], 'category_id': row['category_id'],
        'category_name': row['category_name'], 'photo_url': row['photo_url'],
        'available': bool(row['available']), 'sort_order': row['sort_order']
    }

SELECT_SQL = '''
SELECT mi.id, mi.name, mi.description, mi.price, mi.category_id, c.name AS category_name,
       mi.photo_url, mi.available, mi.sort_order
FROM menu_items mi JOIN categories c ON c.id = mi.category_id
'''

@router.get('')
def list_items():
    conn = get_db()
    rows = conn.execute(SELECT_SQL + ' ORDER BY c.sort_order, mi.sort_order, mi.name').fetchall()
    conn.close()
    return [row_to_item(r) for r in rows]

@router.get('/{item_id}')
def get_item(item_id: int):
    conn = get_db()
    row = conn.execute(SELECT_SQL + ' WHERE mi.id = ?', (item_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='Item not found')
    return row_to_item(row)

@router.post('')
def create_item(payload: MenuItemInput):
    conn = get_db()
    cur = conn.execute(
        '''INSERT INTO menu_items (name, description, price, category_id, photo_url, available, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (payload.name, payload.description, payload.price, payload.category_id, payload.photo_url, int(payload.available), payload.sort_order)
    )
    conn.commit()
    row = conn.execute(SELECT_SQL + ' WHERE mi.id = ?', (cur.lastrowid,)).fetchone()
    conn.close()
    return row_to_item(row)

@router.put('/{item_id}')
def update_item(item_id: int, payload: MenuItemInput):
    conn = get_db()
    if not conn.execute('SELECT id FROM menu_items WHERE id = ?', (item_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='Item not found')
    conn.execute(
        '''UPDATE menu_items SET name=?, description=?, price=?, category_id=?, photo_url=?, available=?, sort_order=? WHERE id=?''',
        (payload.name, payload.description, payload.price, payload.category_id, payload.photo_url, int(payload.available), payload.sort_order, item_id)
    )
    conn.commit()
    row = conn.execute(SELECT_SQL + ' WHERE mi.id = ?', (item_id,)).fetchone()
    conn.close()
    return row_to_item(row)

@router.patch('/{item_id}/availability')
def toggle_availability(item_id: int):
    conn = get_db()
    row = conn.execute('SELECT available FROM menu_items WHERE id = ?', (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='Item not found')
    conn.execute('UPDATE menu_items SET available = ? WHERE id = ?', (0 if row['available'] else 1, item_id))
    conn.commit()
    updated = conn.execute(SELECT_SQL + ' WHERE mi.id = ?', (item_id,)).fetchone()
    conn.close()
    return row_to_item(updated)

@router.delete('/{item_id}')
def delete_item(item_id: int):
    conn = get_db()
    conn.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return {'ok': True}
