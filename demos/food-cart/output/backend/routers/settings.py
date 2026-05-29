from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import AdminAuthInput, AdminAuthResponse, Settings, SettingsInput

router = APIRouter(prefix='/api/settings', tags=['settings'])


@router.get('', response_model=Settings)
def get_settings():
    conn = get_db()
    row = conn.execute(
        '''
        SELECT cart_name, tagline, CAST(is_open AS BOOLEAN) AS is_open,
               estimated_wait_minutes, admin_pin
        FROM settings WHERE id = 1
        '''
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='Settings not found')
    return dict(row)


@router.put('', response_model=Settings)
def update_settings(payload: SettingsInput):
    conn = get_db()
    conn.execute(
        '''
        UPDATE settings
        SET cart_name = ?, tagline = ?, is_open = ?, estimated_wait_minutes = ?, admin_pin = ?
        WHERE id = 1
        ''',
        (
            payload.cart_name,
            payload.tagline,
            int(payload.is_open),
            payload.estimated_wait_minutes,
            payload.admin_pin,
        ),
    )
    conn.commit()
    row = conn.execute(
        '''
        SELECT cart_name, tagline, CAST(is_open AS BOOLEAN) AS is_open,
               estimated_wait_minutes, admin_pin
        FROM settings WHERE id = 1
        '''
    ).fetchone()
    conn.close()
    return dict(row)


@router.post('/verify-pin', response_model=AdminAuthResponse)
def verify_pin(payload: AdminAuthInput):
    conn = get_db()
    row = conn.execute('SELECT admin_pin FROM settings WHERE id = 1').fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='Settings not found')
    return {'success': row['admin_pin'] == payload.pin}
