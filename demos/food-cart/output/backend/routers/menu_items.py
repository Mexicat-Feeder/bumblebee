from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import MenuItem, MenuItemInput

router = APIRouter(prefix='/api/menu-items', tags=['menu-items'])


SELECT_SQL = '''
SELECT m.id, m.name, m.description, m.price, m.category_id, c.name AS category_name,
       m.photo_url, CAST(m.available AS BOOLEAN) AS available, m.sort_order
FROM menu_items m
JOIN categories c ON c.id = m.category_id
'''


@router.get('', response_model=list[MenuItem])
def list_menu_items():
    conn = get_db()
    rows = conn.execute(
        SELECT_SQL + ' ORDER BY c.sort_order, m.sort_order, m.id'
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get('/{item_id}', response_model=MenuItem)
def get_menu_item(item_id: int):
    conn = get_db()
    row = conn.execute(
        SELECT_SQL + ' WHERE m.id = ?',
        (item_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='Menu item not found')
    return dict(row)


@router.post('', response_model=MenuItem)
def create_menu_item(payload: MenuItemInput):
    conn = get_db()
    category = conn.execute(
        'SELECT id FROM categories WHERE id = ?',
        (payload.category_id,),
    ).fetchone()
    if not category:
        conn.close()
        raise HTTPException(status_code=400, detail='Category not found')
    cursor = conn.execute(
        '''
        INSERT INTO menu_items
        (name, description, price, category_id, photo_url, available, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            payload.name,
            payload.description,
            payload.price,
            payload.category_id,
            payload.photo_url,
            int(payload.available),
            payload.sort_order,
        ),
    )
    conn.commit()
    row = conn.execute(
        SELECT_SQL + ' WHERE m.id = ?',
        (cursor.lastrowid,),
    ).fetchone()
    conn.close()
    return dict(row)


@router.put('/{item_id}', response_model=MenuItem)
def update_menu_item(item_id: int, payload: MenuItemInput):
    conn = get_db()
    existing = conn.execute('SELECT id FROM menu_items WHERE id = ?', (item_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail='Menu item not found')
    conn.execute(
        '''
        UPDATE menu_items
        SET name = ?, description = ?, price = ?, category_id = ?, photo_url = ?, available = ?, sort_order = ?
        WHERE id = ?
        ''',
        (
            payload.name,
            payload.description,
            payload.price,
            payload.category_id,
            payload.photo_url,
            int(payload.available),
            payload.sort_order,
            item_id,
        ),
    )
    conn.commit()
    row = conn.execute(SELECT_SQL + ' WHERE m.id = ?', (item_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete('/{item_id}', response_model=MenuItem)
def delete_menu_item(item_id: int):
    conn = get_db()
    row = conn.execute(SELECT_SQL + ' WHERE m.id = ?', (item_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='Menu item not found')
    conn.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return dict(row)
