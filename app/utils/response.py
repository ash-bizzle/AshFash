from flask import jsonify


def success_response(data, meta=None, status_code=200):
    payload = {'success': True, 'data': data, 'error': None}
    if meta is not None:
        payload['meta'] = meta
    return jsonify(payload), status_code


def error_response(message, status_code=400):
    return jsonify({'success': False, 'data': None, 'error': message}), status_code
