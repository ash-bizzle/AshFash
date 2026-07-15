from unittest.mock import patch, MagicMock
from app.models.category import Category
from app.models.product import Product


MOCK_CATEGORIES_RESPONSE = {
    'itemTypes': [{
        'categories': [{
            'id': 4172,
            'label': 'Dresses',
            'link': '/women/dresses/',
            'children': [{
                'id': 6020,
                'label': 'Midi Dresses',
                'link': '/women/dresses/midi/',
            }],
        }],
    }],
}

MOCK_PRODUCTS_RESPONSE = {
    'products': [{
        'id': 12345,
        'name': 'Floral Midi Dress',
        'brandName': 'ASOS DESIGN',
        'imageUrl': 'images.asos.com/floral.jpg',
        'url': '/asos/floral-midi-dress/',
        'colour': 'Pink',
        'gender': 'Women',
        'price': {
            'current': {'value': 45.00},
            'isMarkedDown': False,
        },
    }],
}


def test_sync_categories(app, db):
    with app.app_context():
        with patch('app.services.asos_client.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = MOCK_CATEGORIES_RESPONSE
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            from app.services.sync_service import sync_categories
            log = sync_categories()
            db.session.commit()

        assert log.status == 'success'
        assert Category.query.filter_by(external_id='4172').first() is not None
        assert Category.query.filter_by(external_id='6020').first() is not None


def test_sync_products_for_category(app, db, sample_category):
    with app.app_context():
        with patch('app.services.asos_client.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = MOCK_PRODUCTS_RESPONSE
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            from app.services.sync_service import sync_products_for_category
            log = sync_products_for_category(sample_category.external_id)
            db.session.commit()

        assert log.status == 'success'
        assert log.records_inserted == 1
        product = Product.query.filter_by(external_id='12345').first()
        assert product is not None
        assert product.brand == 'ASOS DESIGN'
        assert float(product.price_amount) == 45.0


def test_sync_products_updates_existing(app, db, sample_product):
    with app.app_context():
        updated_response = {
            'products': [{
                **MOCK_PRODUCTS_RESPONSE['products'][0],
                'id': int(sample_product.external_id.replace('prod-', '0')),
                'name': 'Updated Dress Name',
            }]
        }
        updated_response['products'][0]['id'] = sample_product.external_id

        with patch('app.services.asos_client.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {'products': [{
                'id': sample_product.external_id,
                'name': 'Updated Dress Name',
                'brandName': sample_product.brand,
                'imageUrl': 'images.asos.com/new.jpg',
                'colour': 'Blue',
                'gender': 'Women',
                'price': {'current': {'value': 55.00}, 'isMarkedDown': False},
            }]}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            from app.services.sync_service import sync_products_for_category
            log = sync_products_for_category(sample_product.category_id)
            db.session.commit()

        assert log.records_updated == 1
        assert log.records_inserted == 0
