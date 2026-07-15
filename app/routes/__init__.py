from app.routes import health, products, categories, filters, admin


def register_blueprints(app):
    prefix = '/api/v1'
    app.register_blueprint(health.bp, url_prefix=prefix)
    app.register_blueprint(products.bp, url_prefix=prefix)
    app.register_blueprint(categories.bp, url_prefix=prefix)
    app.register_blueprint(filters.bp, url_prefix=prefix)
    app.register_blueprint(admin.bp, url_prefix=prefix)
