from flask import Blueprint, request
from app.db import get_db
from app.utils.response import success_response

bp = Blueprint('filters', __name__)


@bp.get('/filters')
def get_filters():
    conn = get_db()
    args = request.args

    base_where = 'p.is_active = 1'
    base_params = []
    if category_id := args.get('category_id'):
        try:
            base_where += ' AND p.category_id = %s'
            base_params.append(int(category_id))
        except ValueError:
            pass

    with conn.cursor() as cursor:
        cursor.execute(
            f'SELECT MIN(price_amount) as min_price, MAX(price_amount) as max_price FROM products p WHERE {base_where}',
            tuple(base_params)
        )
        price_row = cursor.fetchone()

        cursor.execute(
            f'SELECT DISTINCT gender FROM products p WHERE {base_where} AND gender IS NOT NULL',
            tuple(base_params)
        )
        genders = [r['gender'] for r in cursor.fetchall()]

        cursor.execute(
            f'SELECT DISTINCT brand FROM products p WHERE {base_where} AND brand IS NOT NULL ORDER BY brand',
            tuple(base_params)
        )
        brands = [r['brand'] for r in cursor.fetchall()]

        cursor.execute(
            f'SELECT DISTINCT colour FROM products p WHERE {base_where} AND colour IS NOT NULL ORDER BY colour',
            tuple(base_params)
        )
        colours = [r['colour'] for r in cursor.fetchall()]

        cursor.execute(
            f'''SELECT DISTINCT ps.size_label
                FROM product_sizes ps
                JOIN products p ON p.id = ps.product_id
                WHERE {base_where}
                ORDER BY ps.size_label''',
            tuple(base_params)
        )
        sizes = [r['size_label'] for r in cursor.fetchall()]

    return success_response({
        'brands': brands,
        'genders': genders,
        'colours': colours,
        'sizes': sizes,
        'price_range': {
            'min': float(price_row['min_price']) if price_row['min_price'] is not None else None,
            'max': float(price_row['max_price']) if price_row['max_price'] is not None else None,
        },
    })
