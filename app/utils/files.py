import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_filename(filename: str) -> str:
    from uuid import uuid4
    ext = filename.rsplit(".", 1)[1].lower()
    return f"{uuid4().hex}.{ext}"