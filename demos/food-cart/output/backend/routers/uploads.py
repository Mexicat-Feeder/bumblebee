import os
import shutil
import uuid
from fastapi import APIRouter, File, HTTPException, UploadFile
from database import UPLOADS_DIR

router = APIRouter(prefix='/api/uploads', tags=['uploads'])


@router.post('')
def upload_file(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='Only image uploads are allowed')
    data = file.file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='File exceeds 5MB limit')
    ext = os.path.splitext(file.filename or '')[1] or '.jpg'
    filename = f'{uuid.uuid4().hex}{ext}'
    path = os.path.join(UPLOADS_DIR, filename)
    with open(path, 'wb') as output:
        output.write(data)
    return {'url': f'/uploads/{filename}'}
