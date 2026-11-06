import os
from dotenv import load_dotenv

# Must run before `app.config` is imported - config.py reads env vars at
# module-import time, so loading .env any later means every setting in it
# (DATABASE_URL, RAPIDAPI_KEY, ANTHROPIC_API_KEY, ...) silently falls back
# to its hardcoded default instead.
load_dotenv()

from flask import Flask
from flask_cors import CORS

from app.config import config_map
from app.db import close_db


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config_map.get(config_name, config_map['development']))

    CORS(app, origins=app.config['CORS_ORIGINS'])
    app.teardown_appcontext(close_db)

    from app.routes import register_blueprints
    register_blueprints(app)

    return app
