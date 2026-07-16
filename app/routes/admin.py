from flask import Blueprint, request, current_app
from app.db import get_db
from app.models.sync_log import rate_tracker_status, sync_log_to_dict
from app.utils.response import success_response, error_response

bp = Blueprint('admin', __name__)


def _check_admin_key():
    key = request.headers.get('X-Admin-Key', '')
    if key != current_app.config['ADMIN_SECRET_KEY']:
        return error_response('Unauthorized', 401)
    return None


@bp.post('/admin/sync/categories')
def sync_categories():
    if err := _check_admin_key():
        return err
    try:
        from app.services.sync_service import sync_categories as _sync
        log = _sync()
        return success_response(log)
    except Exception as e:
        return error_response(str(e), 500)


@bp.post('/admin/sync/products')
def sync_products():
    if err := _check_admin_key():
        return err
    data = request.get_json(silent=True) or {}
    query = data.get('query')
    if not query:
        return error_response('query is required in request body', 400)
    max_pages = int(data.get('max_pages', 2))
    try:
        from app.services.sync_service import sync_products_for_category
        log = sync_products_for_category(query, max_pages=max_pages)
        return success_response(log)
    except Exception as e:
        return error_response(str(e), 500)


@bp.post('/admin/sync/all')
def sync_all():
    if err := _check_admin_key():
        return err
    data = request.get_json(silent=True) or {}
    max_pages = int(data.get('max_pages', 1))

    from app.services.sync_service import sync_products_for_category, SYNC_SEARCH_TERMS
    results = []
    total_inserted = total_updated = total_api_calls = 0

    for term in SYNC_SEARCH_TERMS:
        try:
            log = sync_products_for_category(term, max_pages=max_pages)
            total_inserted += log.get('records_inserted', 0)
            total_updated += log.get('records_updated', 0)
            total_api_calls += log.get('api_calls_used', 0)
            results.append({'term': term, 'status': 'ok', 'inserted': log.get('records_inserted', 0)})
        except Exception as e:
            results.append({'term': term, 'status': 'error', 'error': str(e)})

    return success_response({
        'terms_synced': len(SYNC_SEARCH_TERMS),
        'total_inserted': total_inserted,
        'total_updated': total_updated,
        'total_api_calls': total_api_calls,
        'details': results,
    })


@bp.get('/admin/sync/status')
def sync_status():
    if err := _check_admin_key():
        return err
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM sync_logs ORDER BY started_at DESC LIMIT 10')
        logs = [sync_log_to_dict(r) for r in cursor.fetchall()]
        tracker = rate_tracker_status(cursor)
    return success_response({'recent_syncs': logs, 'rate_limit': tracker})


@bp.get('/admin/rate-limit')
def rate_limit():
    if err := _check_admin_key():
        return err
    conn = get_db()
    with conn.cursor() as cursor:
        tracker = rate_tracker_status(cursor)
    return success_response(tracker)

@bp.get('/admin/removeItem/<external_id>')
def remove_item(external_id):
    if err := _check_admin_key():
        return err
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM products p WHERE external_id = %s", (external_id,))
        if not cursor.fetchone():
            return error_response('Product not found', 404)
        
        cursor.execute("UPDATE products SET is_active = 0 WHERE external_id = %s", (external_id,))
        conn.commit()
    return success_response({'deactivated': external_id})

@bp.post('/admin/products/<external_id>/sizes')
def add_size(external_id):
    if err := _check_admin_key():
        return err
    data = request.get_json(silent=True) or {}
    size_label = data.get('size_label')
    if not size_label:
        return error_response('size_label is required', 400)
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM products WHERE external_id = %s", (external_id,))
        product = cursor.fetchone()
        if not product:
            return error_response('Product not found', 404)
        product_id = product['id']

        cursor.execute(
            "SELECT COUNT(*) AS total FROM product_sizes WHERE product_id = %s AND size_label = %s", (product_id, size_label)
        )
        count = cursor.fetchone()['total']
        if count == 0:
            cursor.execute("INSERT INTO product_sizes(product_id, size_label, is_available) VALUES (%s, %s, 1)", (product_id, size_label))
        else:
            return error_response('Size already exists', 400)
        conn.commit()
        return success_response('Size updated', 200)
