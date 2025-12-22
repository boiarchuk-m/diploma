from flask import Blueprint

test = Blueprint('test', __name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import offers