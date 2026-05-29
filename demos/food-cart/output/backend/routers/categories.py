from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import CategoryInput

router = APIRouter(prefix='/api/categories', tags=['categories'])

def row_to_category(row):
    return {'id': row['id'], 'name': row['name'], 'sort_order': row['sort_order']}

@router.get('')
def list_categories():
    conn = get_db()
    rows = conn.execute('SELECT id, name, sort_order FROM categories ORDER BY sort_order, name').fetchall()
    conn.close()
    return [row_to_category(r) for r in rows]

@router.post('')
def create_category(payload: CategoryInput):
    conn = get_db()
    cur = conn.execute('INSERT INTO categories (name, sort_order) VALUES (?, ?)', (payload.name, payload.sort_order))
    conn.commit()
    row = conn.execute('SELECT id, name, sort_order FROM categories WHERE id = ?', (cur.lastrowid,)).fetchone()
    conn.close()
    return row_to_category(row)

@router.put('/{category_id}')
def update_category(category_id: int, payload: CategoryInput):
    conn = get_db()
    existing = conn.execute('SELECT id FROM categories WHERE id = ?', (category_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail='Category not found')
    conn.execute('UPDATE categories SET name = ?, sort_order = ? WHERE id = ?', (payload.name, payload.sort_order, category_id))
    conn.commit()
    row = conn.execute('SELECT id, name, sort_order FROM categories WHERE id = ?', (category_id,)).fetchone()
    conn.close()
    return row_to_category(row)

@router.delete('/{category_id}')
def delete_category(category_id: int):
    conn = get_db()
    used = conn.execute('SELECT COUNT(*) AS c FROM menu_items WHERE category_id = ?', (category_id,)).fetchone()['c']
    if used:
        conn.close()
        raise HTTPException(status_code=400, detail='Category has menu items')
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    return {'ok': True}
