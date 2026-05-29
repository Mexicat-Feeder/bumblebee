from fastapi import APIRouter, HTTPException
from database import get_db
from realtime import manager
from schemas import CreateOrderRequest, UpdateOrderStatus

router = APIRouter(prefix='/api/orders', tags=['orders'])

def fetch_order(conn, order_id: int):
    order = conn.execute('SELECT id, order_number, customer_name, status, created_at, updated_at FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        return None
    items = conn.execute('SELECT id, order_id, item_id, item_name, item_price, quantity FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
    item_list = [dict(r) for r in items]
    return {
        'id': order['id'], 'order_number': order['order_number'], 'customer_name': order['customer_name'],
        'status': order['status'], 'created_at': order['created_at'], 'updated_at': order['updated_at'],
        'items': item_list, 'total': sum(i['item_price'] * i['quantity'] for i in item_list)
    }

@router.get('')
def list_orders():
    conn = get_db()
    rows = conn.execute('SELECT id FROM orders ORDER BY id DESC').fetchall()
    orders = [fetch_order(conn, r['id']) for r in rows]
    conn.close()
    return orders

@router.get('/{order_id}')
def get_order(order_id: int):
    conn = get_db()
    order = fetch_order(conn, order_id)
    conn.close()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    return order

@router.post('')
async def create_order(payload: CreateOrderRequest):
    if not payload.customer_name.strip() or not payload.items:
        raise HTTPException(status_code=400, detail='Name and items are required')
    conn = get_db()
    settings = conn.execute('SELECT is_open FROM settings WHERE id = 1').fetchone()
    if not settings or not settings['is_open']:
        conn.close()
        raise HTTPException(status_code=400, detail='Ordering is closed')
    cur = conn.execute('INSERT INTO orders (order_number, customer_name) VALUES (?, ?)', ('PENDING', payload.customer_name.strip()))
    order_id = cur.lastrowid
    order_number = f'#{order_id:03d}'
    conn.execute('UPDATE orders SET order_number = ? WHERE id = ?', (order_number, order_id))
    for line in payload.items:
        item = conn.execute('SELECT id, name, price, available FROM menu_items WHERE id = ?', (line.item_id,)).fetchone()
        if not item or not item['available'] or line.quantity < 1:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail='Invalid or unavailable item')
        conn.execute(
            'INSERT INTO order_items (order_id, item_id, item_name, item_price, quantity) VALUES (?, ?, ?, ?, ?)',
            (order_id, item['id'], item['name'], item['price'], line.quantity)
        )
    conn.commit()
    order = fetch_order(conn, order_id)
    conn.close()
    await manager.broadcast_admin({'type': 'order_created', 'order': order})
    return order

@router.patch('/{order_id}/status')
async def update_status(order_id: int, payload: UpdateOrderStatus):
    conn = get_db()
    if not conn.execute('SELECT id FROM orders WHERE id = ?', (order_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail='Order not found')
    conn.execute('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (payload.status, order_id))
    conn.commit()
    order = fetch_order(conn, order_id)
    conn.close()
    await manager.broadcast_order(order_id, {'type': 'order_updated', 'order': order})
    await manager.broadcast_admin({'type': 'order_updated', 'order': order})
    return order
