def test_list_products_empty(client):
    resp = client.get('/api/v1/products')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['data'] == []
    assert data['meta']['total'] == 0


def test_list_products_returns_item(client, sample_product):
    resp = client.get('/api/v1/products')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['meta']['total'] == 1
    assert data['data'][0]['external_id'] == 'prod-001'


def test_filter_by_brand(client, sample_product):
    resp = client.get('/api/v1/products?brand=ASOS+DESIGN')
    assert resp.get_json()['meta']['total'] == 1

    resp = client.get('/api/v1/products?brand=Unknown')
    assert resp.get_json()['meta']['total'] == 0


def test_filter_by_gender(client, sample_product):
    resp = client.get('/api/v1/products?gender=women')
    assert resp.get_json()['meta']['total'] == 1

    resp = client.get('/api/v1/products?gender=men')
    assert resp.get_json()['meta']['total'] == 0


def test_filter_by_price(client, sample_product):
    resp = client.get('/api/v1/products?min_price=10&max_price=50')
    assert resp.get_json()['meta']['total'] == 1

    resp = client.get('/api/v1/products?min_price=100')
    assert resp.get_json()['meta']['total'] == 0


def test_filter_by_colour(client, sample_product):
    resp = client.get('/api/v1/products?colour=Pink')
    assert resp.get_json()['meta']['total'] == 1


def test_filter_by_size(client, sample_product):
    resp = client.get('/api/v1/products?size=S')
    assert resp.get_json()['meta']['total'] == 1

    resp = client.get('/api/v1/products?size=XL')
    assert resp.get_json()['meta']['total'] == 0


def test_get_product_detail(client, sample_product):
    resp = client.get('/api/v1/products/prod-001')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['external_id'] == 'prod-001'
    assert 'images' in data
    assert 'sizes' in data
    assert len(data['sizes']) == 2


def test_get_product_not_found(client):
    resp = client.get('/api/v1/products/nonexistent')
    assert resp.status_code == 404
    assert resp.get_json()['success'] is False


def test_search_requires_q(client):
    resp = client.get('/api/v1/products/search')
    assert resp.status_code == 400


def test_health(client):
    resp = client.get('/api/v1/health')
    assert resp.status_code == 200
    assert resp.get_json()['data']['status'] == 'ok'
