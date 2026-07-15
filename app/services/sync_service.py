import json
from datetime import datetime
from flask import current_app
from app.db import get_db
from app.models.sync_log import (
    sync_log_start, sync_log_complete, sync_log_fail, sync_log_to_dict,
)
from app.services.asos_client import AsosClient

UNIQLO_CATEGORIES = [
    {'external_id': 'women',         'name': 'Women',     'slug': 'women',          'gender': 'women',  'parent': None},
    {'external_id': 'men',           'name': 'Men',       'slug': 'men',            'gender': 'men',    'parent': None},
    {'external_id': 'kids',          'name': 'Kids',      'slug': 'kids',           'gender': 'kids',   'parent': None},
    {'external_id': 'unisex',        'name': 'Unisex',    'slug': 'unisex',         'gender': 'unisex', 'parent': None},
    {'external_id': 'women-tops',    'name': 'Tops',      'slug': 'women-tops',     'gender': 'women',  'parent': 'women'},
    {'external_id': 'women-bottoms', 'name': 'Bottoms',   'slug': 'women-bottoms',  'gender': 'women',  'parent': 'women'},
    {'external_id': 'women-dresses', 'name': 'Dresses',   'slug': 'women-dresses',  'gender': 'women',  'parent': 'women'},
    {'external_id': 'women-outerwear','name': 'Outerwear','slug': 'women-outerwear','gender': 'women',  'parent': 'women'},
    {'external_id': 'men-tops',      'name': 'Tops',      'slug': 'men-tops',       'gender': 'men',    'parent': 'men'},
    {'external_id': 'men-bottoms',   'name': 'Bottoms',   'slug': 'men-bottoms',    'gender': 'men',    'parent': 'men'},
    {'external_id': 'men-outerwear', 'name': 'Outerwear', 'slug': 'men-outerwear',  'gender': 'men',    'parent': 'men'},
]

SYNC_SEARCH_TERMS = [
    'shirt', 'pants', 'dress', 'jacket', 'sweater',
    'skirt', 'coat', 'jeans', 'shorts', 'cardigan',
]


def sync_categories():
    conn = get_db()
    inserted = updated = 0

    with conn.cursor() as cursor:
        log_id = sync_log_start(cursor, 'full_categories')
        try:
            for cat_data in UNIQLO_CATEGORIES:
                result = _upsert_category(cursor, cat_data)
                if result == 'inserted':
                    inserted += 1
                else:
                    updated += 1
            sync_log_complete(cursor, log_id, inserted=inserted, updated=updated, fetched=len(UNIQLO_CATEGORIES))
            conn.commit()
        except Exception as e:
            sync_log_fail(cursor, log_id, e)
            conn.rollback()
            raise

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM sync_logs WHERE id = %s', (log_id,))
        return sync_log_to_dict(cursor.fetchone())


def sync_products_for_category(query, max_pages=2):
    conn = get_db()
    client = AsosClient()
    inserted = updated = fetched = api_calls = 0

    with conn.cursor() as cursor:
        log_id = sync_log_start(cursor, 'category_products', query)
        try:
            for page in range(1, max_pages + 1):
                data = client.search_products(query, page=page)
                api_calls += 1
                payload = data.get('data', {})
                products = payload.get('products', [])
                fetched += len(products)
                for item in products:
                    result = _upsert_product(cursor, item)
                    if result == 'inserted':
                        inserted += 1
                    elif result == 'updated':
                        updated += 1
                if not payload.get('pagination', {}).get('hasNextPage'):
                    break

            sync_log_complete(cursor, log_id, inserted=inserted, updated=updated, fetched=fetched, api_calls=api_calls)
            conn.commit()
        except Exception as e:
            sync_log_fail(cursor, log_id, e)
            conn.rollback()
            raise

    with conn.cursor() as cursor:
        cursor.execute('SELECT * FROM sync_logs WHERE id = %s', (log_id,))
        return sync_log_to_dict(cursor.fetchone())


def cache_search_results(query):
    conn = get_db()
    client = AsosClient()
    inserted = updated = fetched = 0

    with conn.cursor() as cursor:
        log_id = sync_log_start(cursor, 'search_cache', query)
        try:
            data = client.search_products(query, page=1)
            products = data.get('data', {}).get('products', [])
            fetched = len(products)
            for item in products:
                result = _upsert_product(cursor, item)
                if result == 'inserted':
                    inserted += 1
                else:
                    updated += 1
            sync_log_complete(cursor, log_id, inserted=inserted, updated=updated, fetched=fetched, api_calls=1)
            conn.commit()
        except Exception as e:
            sync_log_fail(cursor, log_id, e)
            conn.rollback()
            raise


# --- helpers ---

def _upsert_category(cursor, cat_data):
    cursor.execute(
        'SELECT id FROM categories WHERE external_id = %s',
        (cat_data['external_id'],)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            'UPDATE categories SET name = %s, gender = %s WHERE external_id = %s',
            (cat_data['name'], cat_data['gender'], cat_data['external_id'])
        )
        return 'updated'

    parent_id = None
    if cat_data.get('parent'):
        cursor.execute('SELECT id FROM categories WHERE external_id = %s', (cat_data['parent'],))
        parent = cursor.fetchone()
        if parent:
            parent_id = parent['id']

    cursor.execute(
        '''INSERT INTO categories (external_id, name, slug, gender, parent_id, is_active, display_order)
           VALUES (%s, %s, %s, %s, %s, 1, 0)''',
        (cat_data['external_id'], cat_data['name'], cat_data['slug'], cat_data['gender'], parent_id)
    )
    return 'inserted'


def _upsert_product(cursor, item):
    external_id = str(item.get('productId', ''))
    if not external_id:
        return 'skipped'

    name = item.get('name', '')
    gender = _map_gender(item.get('genderCategory', '') or item.get('genderName', ''))

    prices = item.get('prices', {})
    try:
        price_amount = float(prices.get('base', {}).get('value', 0))
    except (ValueError, TypeError):
        price_amount = None

    try:
        promo = prices.get('promo')
        sale_price = float(promo.get('value')) if promo else None
    except (ValueError, TypeError):
        sale_price = None

    currency = prices.get('base', {}).get('currency', {}).get('code', 'USD')

    images_main = item.get('images', {}).get('main', {})
    primary_image = None
    for color_data in images_main.values():
        if isinstance(color_data, dict) and color_data.get('image'):
            primary_image = color_data['image']
            break

    external_url = f"https://www.uniqlo.com{item.get('url', '')}" if item.get('url') else None
    colours = item.get('colors', [])
    colour = colours[0].get('name') if colours else None
    category_id = _resolve_category(cursor, gender)

    cursor.execute('SELECT id FROM products WHERE external_id = %s', (external_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            '''UPDATE products SET name=%s, price_amount=%s, sale_price_amount=%s,
               primary_image_url=%s, external_url=%s, colour=%s, category_id=%s,
               gender=%s, raw_data=%s, last_synced_at=NOW()
               WHERE external_id=%s''',
            (name, price_amount, sale_price, primary_image, external_url,
             colour, category_id, gender, json.dumps(item), external_id)
        )
        return 'updated'

    cursor.execute(
        '''INSERT INTO products
           (external_id, name, brand, description, price_amount, price_currency,
            sale_price_amount, primary_image_url, external_url, colour, gender,
            category_id, is_active, raw_data, last_synced_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,NOW())''',
        (external_id, name, 'Uniqlo', '', price_amount, currency,
         sale_price, primary_image, external_url, colour, gender,
         category_id, json.dumps(item))
    )
    product_id = cursor.lastrowid

    if primary_image:
        cursor.execute(
            'INSERT INTO product_images (product_id, image_url, is_primary, display_order) VALUES (%s,%s,1,0)',
            (product_id, primary_image)
        )

    for i, (color_code, color_data) in enumerate(images_main.items()):
        if isinstance(color_data, dict) and color_data.get('image') and color_data['image'] != primary_image:
            cursor.execute(
                'INSERT INTO product_images (product_id, image_url, is_primary, display_order) VALUES (%s,%s,0,%s)',
                (product_id, color_data['image'], i + 1)
            )

    for size in item.get('sizes', []):
        size_name = size.get('name', '')
        if size_name:
            cursor.execute(
                'INSERT INTO product_sizes (product_id, size_label, is_available) VALUES (%s,%s,1)',
                (product_id, size_name)
            )

    return 'inserted'


def _resolve_category(cursor, gender):
    if not gender:
        return None
    cursor.execute('SELECT id FROM categories WHERE external_id = %s', (gender,))
    row = cursor.fetchone()
    return row['id'] if row else None


def _map_gender(raw):
    if not raw:
        return 'unisex'
    raw = raw.upper()
    if 'WOMEN' in raw or 'FEMALE' in raw or 'GIRL' in raw:
        return 'women'
    if 'MEN' in raw or 'MALE' in raw or 'BOY' in raw:
        return 'men'
    if 'KID' in raw or 'CHILD' in raw or 'BABY' in raw:
        return 'kids'
    return 'unisex'
