import pymysql
import pymysql.cursors
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=current_app.config['DB_HOST'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME'],
            port=current_app.config['DB_PORT'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            charset='utf8mb4',
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
