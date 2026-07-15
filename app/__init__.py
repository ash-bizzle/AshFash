import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import config_map
from app.db import close_db

load_dotenv()


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
