import os
import urllib.parse


def _parse_db_url(url):
    parsed = urllib.parse.urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 3306,
        'user': parsed.username or 'root',
        'password': urllib.parse.unquote(parsed.password or ''),
        'name': parsed.path.lstrip('/'),
    }


_db = _parse_db_url(os.getenv('DATABASE_URL', 'mysql+pymysql://root@localhost:3306/ashfash_db'))


class BaseConfig:
    DB_HOST = _db['host']
    DB_PORT = _db['port']
    DB_USER = _db['user']
    DB_PASSWORD = _db['password']
    DB_NAME = _db['name']
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
    RAPIDAPI_HOST = os.getenv('RAPIDAPI_HOST', 'uniqlo-eccommerce.p.rapidapi.com')
    RAPIDAPI_BASE_URL = 'https://uniqlo-eccommerce.p.rapidapi.com'
    PRODUCT_CACHE_TTL_DAYS = int(os.getenv('PRODUCT_CACHE_TTL_DAYS', 7))
    API_MONTHLY_LIMIT = int(os.getenv('API_MONTHLY_LIMIT', 500))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173')
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'change_me')


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    DB_NAME = os.getenv('TEST_DB_NAME', 'ashfash_test')
    ADMIN_SECRET_KEY = 'test-secret'


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
