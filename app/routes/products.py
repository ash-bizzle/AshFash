from flask import Blueprint, request
from app.db import get_db
from app.utils.response import success_response, error_response

bp = Blueprint('products', __name__)


@bp.get('/products')
def list_products():
    where, params = _build_filters()
    sort_clause = _sort_clause()
    page, page_size = _pagination_params()
    limit = page_size
    offset = (page - 1) * page_size

    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            f'''SELECT COUNT(*) as total
                FROM products p
                WHERE {where}''',
            params
        )
        total = cursor.fetchone()['total']

        cursor.execute(
            f'''SELECT p.id, p.external_id, p.name, p.brand, p.external_url,
                       p.primary_image_url, p.price_amount, p.price_currency,
                       p.sale_price_amount, p.category_id, p.gender, p.colour
                FROM products p
                WHERE {where}
                ORDER BY {sort_clause}
                LIMIT %s OFFSET %s''',
            params + (limit, offset)
        )
        rows = cursor.fetchall()

    meta = {
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': (total + page_size - 1) // page_size,
    }
    return success_response([_format_product(r) for r in rows], meta=meta)

@bp.get('/products/sale_items')
def sale_products():
    # make a call to the db then get only the items on sale
    # return them
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            f'''SELECT * FROM products p
            WHERE p.is_active = 1 AND p.sale_price_amount is NOT NULL
            ORDER BY p.sale_price_amount ASC'''
        )
        rows = cursor.fetchall()

    return success_response([_format_product(r) for r in rows])

@bp.get('/products/recent')
def recent_products():
    # make a call to the db to only return the products posted within the last 7 days
    # return them
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            '''SELECT * FROM products p
            WHERE p.is_active = 1 AND p.created_at >= CURRENT_TIMESTAMP - INTERVAL 7 DAY
            ORDER BY p.created_at ASC
            '''
        )
        rows = cursor.fetchall()

    return success_response([_format_product(r) for r in rows])

@bp.get('/products/random')
def random_product():
    # make a call to the db to only return the products posted within the last 7 days
    # return them
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            '''SELECT * FROM products p
            WHERE p.is_active = 1
            ORDER BY RAND()
            LIMIT 1
            '''
        )
        row = cursor.fetchall()
    if not row:
        return error_response('No products found, 404')
    return success_response([_format_product(r) for r in row])

@bp.get('/products/search')
def search_products():
    q = request.args.get('q', '').strip()
    if not q:
        return error_response('Query parameter "q" is required', 400)

    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT COUNT(*) as total FROM products p WHERE is_active = 1 AND MATCH(name, brand, description) AGAINST (%s IN BOOLEAN MODE)',
            (q,)
        )
        total = cursor.fetchone()['total']

        if total == 0:
            from app.models.sync_log import rate_tracker_has_budget
            if rate_tracker_has_budget(cursor):
                try:
                    from app.services.sync_service import cache_search_results
                    cache_search_results(q)
                    conn.commit()
                except Exception as e:
                    import logging
                    logging.warning(f'Search-miss fallback failed: {e}')

        cursor.execute(
            '''SELECT p.id, p.external_id, p.name, p.brand, p.external_url,
                      p.primary_image_url, p.price_amount, p.price_currency,
                      p.sale_price_amount, p.category_id, p.gender, p.colour
               FROM products p
               WHERE is_active = 1
               AND MATCH(name, brand, description) AGAINST (%s IN BOOLEAN MODE)
               ORDER BY p.created_at DESC''',
            (q,)
        )
        rows = cursor.fetchall()

    return success_response([_format_product(r) for r in rows])

@bp.get('/products/trending')
def get_trending_products():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT * FROM products WHERE is_active = 1 ORDER BY view_count DESC LIMIT 10'
        )
        row = cursor.fetchall()
    if not row:
        return error_response('No products found, 404')
    return success_response([_format_product(r) for r in row])

@bp.get('products/missing_images')
def get_noImage_products():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT * FROM products p WHERE is_active = 1 AND primary_image_url IS NULL'
        )
        row = cursor.fetchall()
    if not row:
        return error_response('No products found, 404')
    return success_response([_format_product(r) for r in row])

@bp.get('/products/<external_id>')
def get_product(external_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT * FROM products WHERE external_id = %s AND is_active = 1',
            (external_id,)
        )
        product = cursor.fetchone()
        if not product:
            return error_response('Product not found', 404)

        cursor.execute(
            'SELECT id, image_url, is_primary, display_order FROM product_images WHERE product_id = %s ORDER BY display_order',
            (product['id'],)
        )
        images = cursor.fetchall()

        cursor.execute(
            'SELECT id, size_label, is_available FROM product_sizes WHERE product_id = %s',
            (product['id'],)
        )
        sizes = cursor.fetchall()

        cursor.execute(
            'UPDATE products SET view_count = view_count + 1 WHERE external_id = %s', (external_id,)
        )
        conn.commit()

    data = _format_product(product)
    data['description'] = product.get('description')
    data['images'] = list(images)
    data['sizes'] = list(sizes)
    return success_response(data)

@bp.get('/categories/<external_id>/children')
def get_child_categories(external_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT id FROM categories WHERE external_id = %s AND is_active = 1',(external_id,)
        )
        parent = cursor.fetchone()
        if not parent:
            # status code must be passed as the 2nd arg, not embedded in the message string
            return error_response('No categories found', 404)
        
        cursor.execute(
            'SELECT id, external_id, name FROM categories WHERE parent_id = %s AND is_active = 1', (parent['id'],)
        )
        cat = cursor.fetchall()
    return success_response(cat)

@bp.get('/brands')
def get_brands():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT DISTINCT brand FROM products p WHERE is_active = 1 AND brand IS NOT NULL'
        )
        row = cursor.fetchall()
        print(row)
    if not row:
        return error_response('No brands found, 404')
    return success_response([r['brand'] for r in row])





# --- helpers ---

def _build_filters():
    args = request.args
    conditions = ['p.is_active = 1']
    params = []

    if category_id := args.get('category_id'):
        try:
            conditions.append('p.category_id = %s')
            params.append(int(category_id))
        except ValueError:
            pass

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

    return ' AND '.join(conditions), tuple(params)


def _pagination_params():
    args = request.args

    try:
        page = int(args.get('page', 1))
    except ValueError:
        page = 1
    if page < 1:
        page = 1

    try:
        page_size = int(args.get('page_size', 20))
    except ValueError:
        page_size = 20
    page_size = max(1, min(page_size, 100))

    return page, page_size


def _sort_clause():
    sort = request.args.get('sort', 'newest')
    if sort == 'price_asc':
        return 'p.price_amount ASC'
    if sort == 'price_desc':
        return 'p.price_amount DESC'
    return 'p.created_at DESC'


def _format_product(row):
    return {
        'id': row['id'],
        'external_id': row['external_id'],
        'name': row['name'],
        'brand': row['brand'],
        'external_url': row['external_url'],
        'primary_image_url': row['primary_image_url'],
        'price_amount': float(row['price_amount']) if row['price_amount'] is not None else None,
        'price_currency': row['price_currency'],
        'sale_price_amount': float(row['sale_price_amount']) if row['sale_price_amount'] is not None else None,
        'category_id': row['category_id'],
        'gender': row['gender'],
        'colour': row['colour'],
    }
