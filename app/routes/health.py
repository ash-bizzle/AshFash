from flask import Blueprint
from app.db import get_db
from app.utils.response import success_response, error_response

bp = Blueprint('health', __name__)


@bp.get('/health')
def health():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
        return success_response({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return error_response(f'Database unavailable: {e}', 503)
