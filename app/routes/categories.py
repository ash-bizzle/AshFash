from flask import Blueprint, request
from app.db import get_db
from app.utils.response import success_response, error_response

bp = Blueprint('categories', __name__)


@bp.get('/categories')
def list_categories():
    conn = get_db()
    gender = request.args.get('gender')
    tree = request.args.get('tree', '').lower() == 'true'

    conditions = ['is_active = 1']
    params = []
    if gender:
        conditions.append("gender IN (%s, 'unisex')")
        params.append(gender)

    where = ' AND '.join(conditions)

    with conn.cursor() as cursor:
        cursor.execute(
            f'SELECT * FROM categories WHERE {where} ORDER BY display_order',
            tuple(params)
        )
        rows = cursor.fetchall()

    if tree:
        by_id = {r['id']: dict(r, children=[]) for r in rows}
        roots = []
        for cat in by_id.values():
            pid = cat['parent_id']
            if pid and pid in by_id:
                by_id[pid]['children'].append(cat)
            else:
                roots.append(cat)
        return success_response(roots)

    return success_response([dict(r) for r in rows])


@bp.get('/categories/<external_id>')
def get_category(external_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT * FROM categories WHERE external_id = %s AND is_active = 1',
            (external_id,)
        )
        row = cursor.fetchone()
    if not row:
        return error_response('Category not found', 404)
    return success_response(dict(row))


@bp.get('/categories/<external_id>/products')
def category_products(external_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT id FROM categories WHERE external_id = %s AND is_active = 1',
            (external_id,)
        )
        cat = cursor.fetchone()
    if not cat:
        return error_response('Category not found', 404)

    conditions = ['p.is_active = 1', 'p.category_id = %s']
    params = [cat['id']]

    args = request.args
    if brand := args.get('brand'):
        conditions.append('p.brand = %s')
        params.append(brand)
    if gender := args.get('gender'):
        conditions.append("p.gender IN (%s, 'unisex')")
        params.append(gender)
    if colour := args.get('colour'):
        conditions.append('p.colour = %s')
        params.append(colour)
    if min_price := args.get('min_price'):
        try:
            conditions.append('p.price_amount >= %s')
            params.append(float(min_price))
        except ValueError:
            pass
    if max_price := args.get('max_price'):
        try:
            conditions.append('p.price_amount <= %s')
            params.append(float(max_price))
        except ValueError:
            pass
    if size := args.get('size'):
        conditions.append(
            'EXISTS (SELECT 1 FROM product_sizes ps WHERE ps.product_id = p.id AND ps.size_label = %s AND ps.is_available = 1)'
        )
        params.append(size)

    sort = args.get('sort', 'newest')
    sort_clause = 'p.price_amount ASC' if sort == 'price_asc' else 'p.price_amount DESC' if sort == 'price_desc' else 'p.created_at DESC'
    where = ' AND '.join(conditions)

    with conn.cursor() as cursor:
        cursor.execute(
            f'''SELECT p.id, p.external_id, p.name, p.brand, p.external_url,
                       p.primary_image_url, p.price_amount, p.price_currency,
                       p.sale_price_amount, p.category_id, p.gender, p.colour
                FROM products p WHERE {where} ORDER BY {sort_clause}''',
            tuple(params)
        )
        rows = cursor.fetchall()

    items = [{
        'id': r['id'], 'external_id': r['external_id'], 'name': r['name'],
        'brand': r['brand'], 'external_url': r['external_url'],
        'primary_image_url': r['primary_image_url'],
        'price_amount': float(r['price_amount']) if r['price_amount'] is not None else None,
        'price_currency': r['price_currency'],
        'sale_price_amount': float(r['sale_price_amount']) if r['sale_price_amount'] is not None else None,
        'category_id': r['category_id'], 'gender': r['gender'], 'colour': r['colour'],
    } for r in rows]

    return success_response(items)
