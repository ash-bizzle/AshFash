from flask import Blueprint, request, current_app
from app.utils.response import success_response, error_response

bp = Blueprint('stylist', __name__)

MAX_MESSAGE_LENGTH = 1000


@bp.post('/stylist')
def ask_stylist():
    if not current_app.config.get('ANTHROPIC_API_KEY'):
        return error_response('Stylist is not configured (missing ANTHROPIC_API_KEY)', 503)

    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return error_response('message is required', 400)
    if len(message) > MAX_MESSAGE_LENGTH:
        return error_response(f'message is too long (max {MAX_MESSAGE_LENGTH} characters)', 400)

    try:
        from app.services.stylist_agent import run_stylist_session
        result = run_stylist_session(message)
    except Exception as e:
        current_app.logger.exception('Stylist session failed')
        return error_response(f'Stylist is temporarily unavailable: {e}', 502)

    return success_response(result)
