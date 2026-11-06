def test_stylist_without_api_key_returns_503(client, app, monkeypatch):
    # Explicitly clear it rather than relying on it being unset - a real
    # ANTHROPIC_API_KEY in .env would otherwise make this call for real.
    monkeypatch.setitem(app.config, 'ANTHROPIC_API_KEY', None)

    resp = client.post('/api/v1/stylist', json={'message': 'something warm for fall'})
    assert resp.status_code == 503
    assert resp.get_json()['success'] is False


def test_stylist_requires_message(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'ANTHROPIC_API_KEY', 'test-key')

    resp = client.post('/api/v1/stylist', json={})
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_stylist_rejects_overlong_message(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'ANTHROPIC_API_KEY', 'test-key')

    resp = client.post('/api/v1/stylist', json={'message': 'x' * 1001})
    assert resp.status_code == 400


def test_stylist_returns_agent_result(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'ANTHROPIC_API_KEY', 'test-key')

    fake_result = {
        'answer': 'The Floral Midi Dress (prod-001) would be perfect for that.',
        'products': [{'external_id': 'prod-001', 'name': 'Floral Midi Dress'}],
    }
    monkeypatch.setattr(
        'app.services.stylist_agent.run_stylist_session',
        lambda message: fake_result,
    )

    resp = client.post('/api/v1/stylist', json={'message': 'something for a wedding'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['data'] == fake_result


def test_stylist_handles_agent_errors(client, app, monkeypatch):
    monkeypatch.setitem(app.config, 'ANTHROPIC_API_KEY', 'test-key')

    def _boom(message):
        raise RuntimeError('upstream exploded')

    monkeypatch.setattr('app.services.stylist_agent.run_stylist_session', _boom)

    resp = client.post('/api/v1/stylist', json={'message': 'something for a wedding'})
    assert resp.status_code == 502
    assert resp.get_json()['success'] is False
