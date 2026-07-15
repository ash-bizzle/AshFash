import pytest
import pymysql
import pymysql.cursors
from app import create_app
from app.db import get_db


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        conn = get_db()
        _apply_schema(conn)
        yield app
        _drop_all(conn)


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        conn = get_db()
        yield conn
        with conn.cursor() as cursor:
            cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
            for table in ('product_sizes', 'product_images', 'products', 'categories', 'sync_logs', 'api_rate_tracker'):
                cursor.execute(f'DELETE FROM {table}')
            cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
        conn.commit()


@pytest.fixture
def sample_category(db):
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO categories (external_id, name, slug, gender) VALUES ('cat-001', 'Dresses', 'dresses', 'women')"
        )
        cat_id = cursor.lastrowid
    db.commit()
    return {'id': cat_id, 'external_id': 'cat-001', 'name': 'Dresses'}


@pytest.fixture
def sample_product(db, sample_category):
    with db.cursor() as cursor:
        cursor.execute(
            '''INSERT INTO products
               (external_id, name, brand, price_amount, price_currency, colour, gender, category_id)
               VALUES ('prod-001', 'Floral Midi Dress', 'Uniqlo', 45.00, 'USD', 'Pink', 'women', %s)''',
            (sample_category['id'],)
        )
        product_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO product_images (product_id, image_url, is_primary, display_order) VALUES (%s, 'https://example.com/img.jpg', 1, 0)",
            (product_id,)
        )
        cursor.execute("INSERT INTO product_sizes (product_id, size_label, is_available) VALUES (%s, 'S', 1)", (product_id,))
        cursor.execute("INSERT INTO product_sizes (product_id, size_label, is_available) VALUES (%s, 'M', 1)", (product_id,))
    db.commit()
    return {'id': product_id, 'external_id': 'prod-001'}


def _apply_schema(conn):
    with open('app/db_schema.sql') as f:
        sql = f.read()
    with conn.cursor() as cursor:
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
        for stmt in sql.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                cursor.execute(stmt)
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
    conn.commit()


def _drop_all(conn):
    with conn.cursor() as cursor:
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
        for table in ('product_sizes', 'product_images', 'products', 'categories', 'sync_logs', 'api_rate_tracker'):
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
    conn.commit()
