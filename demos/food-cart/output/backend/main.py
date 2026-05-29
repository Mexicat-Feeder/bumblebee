import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import UPLOAD_DIR, init_db
from seed import seed_database
from routers import categories, items, orders, settings, ws

app = FastAPI(title='Pop-Up Food Cart API', redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:8000', 'http://127.0.0.1:8000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

init_db()
seed_database()

app.include_router(categories.router)
app.include_router(items.router)
app.include_router(settings.router)
app.include_router(orders.router)
app.include_router(ws.router)

app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')

@app.get('/api/health')
def health():
    return {'ok': True}

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'))

if os.path.isdir(frontend_dist):
    app.mount('/assets', StaticFiles(directory=os.path.join(frontend_dist, 'assets')), name='assets')

    @app.get('/{full_path:path}')
    def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, 'index.html'))
