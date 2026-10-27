
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    with app.app_context():
        from app.models import (
            Produto,
            Doacao,
            FamiliaAtendida,
            MovimentacaoEstoque,
        )
        db.create_all()

    from app.routes import main
    from app.product_routes import products
    from app.donation_routes import donations

    app.register_blueprint(main)
    app.register_blueprint(products)
    app.register_blueprint(donations)

    return app
