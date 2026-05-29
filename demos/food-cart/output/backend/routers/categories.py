from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import Category, CategoryInput

router = APIRouter(prefix='/api/categories', tags=['categories'])


@router.get('', response_model=list[Category])
def list_categories():
    conn = get_db()
    rows = conn.execute(
        'SELECT id, name, sort_order FROM categories ORDER BY sort_order, id'
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post('', response_model=Category)
def create_category(payload: CategoryInput):
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO categories (name, sort_order) VALUES (?, ?)',
        (payload.name, payload.sort_order),
    )
    conn.commit()
    row = conn.execute(
        'SELECT id, name, sort_order FROM categories WHERE id = ?',
        (cursor.lastrowid,),
    ).fetchone()
    conn.close()
    return dict(row)


@router.put('/{category_id}', response_model=Category)
def update_category(category_id: int, payload: CategoryInput):
    conn = get_db()
    existing = conn.execute(
        'SELECT id FROM categories WHERE id = ?',
        (category_id,),
    ).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail='Category not found')
    conn.execute(
        'UPDATE categories SET name = ?, sort_order = ? WHERE id = ?',
        (payload.name, payload.sort_order, category_id),
    )
    conn.commit()
    row = conn.execute(
        'SELECT id, name, sort_order FROM categories WHERE id = ?',
        (category_id,),
    ).fetchone()
    conn.close()
    return dict(row)


@router.delete('/{category_id}', response_model=Category)
def delete_category(category_id: int):
    conn = get_db()
    row = conn.execute(
        'SELECT id, name, sort_order FROM categories WHERE id = ?',
        (category_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail='Category not found')
    item = conn.execute(
        'SELECT id FROM menu_items WHERE category_id = ? LIMIT 1',
        (category_id,),
    ).fetchone()
    if item:
        conn.close()
        raise HTTPException(status_code=400, detail='Category has menu items')
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    return dict(row)
