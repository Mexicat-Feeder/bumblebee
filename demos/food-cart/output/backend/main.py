import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database import UPLOADS_DIR, init_db
from routers.categories import router as categories_router
from routers.menu_items import router as menu_items_router
from routers.orders import router as orders_router
from routers.settings import router as settings_router
from routers.uploads import router as uploads_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, '..', 'frontend', 'dist')

init_db()

app = FastAPI(redirect_slashes=False)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(categories_router)
app.include_router(menu_items_router)
app.include_router(orders_router)
app.include_router(settings_router)
app.include_router(uploads_router)
app.mount('/uploads', StaticFiles(directory=UPLOADS_DIR), name='uploads')


@app.get('/api/health')
def health_check():
    return {'status': 'ok'}


@app.get('/{full_path:path}')
def serve_frontend(full_path: str):
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    asset_path = os.path.join(FRONTEND_DIST, full_path)
    if full_path and os.path.exists(asset_path) and os.path.isfile(asset_path):
        return FileResponse(asset_path)
    return FileResponse(index_path)
