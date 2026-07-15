import requests
from flask import current_app
from app.db import get_db
from app.models.sync_log import RateLimitExceeded, rate_tracker_has_budget, rate_tracker_increment


class AsosClient:
    def __init__(self):
        self.base_url = current_app.config['RAPIDAPI_BASE_URL']
        self.headers = {
            'x-rapidapi-host': current_app.config['RAPIDAPI_HOST'],
            'x-rapidapi-key': current_app.config['RAPIDAPI_KEY'],
        }
        self.timeout = 15

    def _get(self, path, params=None):
        conn = get_db()
        with conn.cursor() as cursor:
            if not rate_tracker_has_budget(cursor):
                raise RateLimitExceeded('Monthly API rate limit reached')
            resp = requests.get(
                f'{self.base_url}{path}',
                headers=self.headers,
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            rate_tracker_increment(cursor)
        return resp.json()

    def search_products(self, query, page=1):
        return self._get('/search', params={'query': query, 'page': page})

    def get_categories(self):
        return self._get('/categories')
