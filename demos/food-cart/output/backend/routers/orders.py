from datetime import datetime
from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import CreateOrderInput, Order, UpdateOrderStatusInput

router = APIRouter(prefix='/api/orders', tags=['orders'])


def _get_order_items(conn, order_id: int):
    rows = conn.execute(
        '''
        SELECT id, order_id, item_id, item_name, item_price, quantity
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
        ''',
        (order_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _get_order(conn, order_id: int):
    row = conn.execute(
        '''
        SELECT id, order_number, customer_name, status, created_at, updated_at
        FROM orders
        WHERE id = ?
        ''',
        (order_id,),
    ).fetchone()
    if not row:
        return None
    order = dict(row)
    order['items'] = _get_order_items(conn, order_id)
    return order


@router.get('', response_model=list[Order])
def list_orders():
    conn = get_db()
    rows = conn.execute(
        'SELECT id FROM orders ORDER BY id DESC'
    ).fetchall()
    orders = [_get_order(conn, row['id']) for row in rows]
    conn.close()
    return orders


@router.get('/{order_id}', response_model=Order)
def get_order(order_id: int):
    conn = get_db()
    order = _get_order(conn, order_id)
    conn.close()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    return order


@router.post('', response_model=Order)
def create_order(payload: CreateOrderInput):
    if not payload.customer_name.strip():
        raise HTTPException(status_code=400, detail='Customer name is required')
    if not payload.items:
        raise HTTPException(status_code=400, detail='Order items are required')
    conn = get_db()
    settings = conn.execute('SELECT is_open FROM settings WHERE id = 1').fetchone()
    if not settings or settings['is_open'] != 1:
        conn.close()
        raise HTTPException(status_code=400, detail='Ordering is currently closed')
    next_id = conn.execute('SELECT COUNT(*) AS count FROM orders').fetchone()['count'] + 1
    order_number = f'#{next_id:03d}'
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        '''
        INSERT INTO orders (order_number, customer_name, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (order_number, payload.customer_name.strip(), 'received', now, now),
    )
    order_id = cursor.lastrowid
    for entry in payload.items:
        item = conn.execute(
            'SELECT id, name, price, available FROM menu_items WHERE id = ?',
            (entry.item_id,),
        ).fetchone()
        if not item:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail='Menu item not found')
        if item['available'] != 1:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail='Menu item unavailable')
        conn.execute(
            '''
            INSERT INTO order_items (order_id, item_id, item_name, item_price, quantity)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (order_id, item['id'], item['name'], item['price'], entry.quantity),
        )
    conn.commit()
    order = _get_order(conn, order_id)
    conn.close()
    return order


@router.patch('/{order_id}/status', response_model=Order)
def update_order_status(order_id: int, payload: UpdateOrderStatusInput):
    if payload.status not in ['received', 'in_progress', 'ready', 'picked_up']:
        raise HTTPException(status_code=400, detail='Invalid status')
    conn = get_db()
    existing = conn.execute('SELECT id FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail='Order not found')
    now = datetime.utcnow().isoformat()
    conn.execute(
        'UPDATE orders SET status = ?, updated_at = ? WHERE id = ?',
        (payload.status, now, order_id),
    )
    conn.commit()
    order = _get_order(conn, order_id)
    conn.close()
    return order
