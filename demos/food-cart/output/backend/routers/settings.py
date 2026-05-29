from fastapi import APIRouter
from database import get_db
from schemas import Settings

router = APIRouter(prefix='/api/settings', tags=['settings'])

def row_to_settings(row):
    return {
        'cart_name': row['cart_name'],
        'tagline': row['tagline'],
        'is_open': bool(row['is_open']),
        'estimated_wait_minutes': row['estimated_wait_minutes'],
        'admin_pin': row['admin_pin']
    }

@router.get('')
def get_settings():
    conn = get_db()
    row = conn.execute('SELECT cart_name, tagline, is_open, estimated_wait_minutes, admin_pin FROM settings WHERE id = 1').fetchone()
    conn.close()
    return row_to_settings(row)

@router.put('')
def update_settings(payload: Settings):
    conn = get_db()
    conn.execute(
        '''UPDATE settings SET cart_name=?, tagline=?, is_open=?, estimated_wait_minutes=?, admin_pin=? WHERE id=1''',
        (payload.cart_name, payload.tagline, int(payload.is_open), payload.estimated_wait_minutes, payload.admin_pin)
    )
    conn.commit()
    row = conn.execute('SELECT cart_name, tagline, is_open, estimated_wait_minutes, admin_pin FROM settings WHERE id = 1').fetchone()
    conn.close()
    return row_to_settings(row)
