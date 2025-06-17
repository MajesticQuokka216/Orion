# myapp/__init__.py

from flask import Flask
from .extensions import db, login_manager, bcrypt, migrate
from .routes import main

def create_app():
    app = Flask(__name__)

    # ——— Configuration ———
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    # ——— Initialize extensions ———
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # ——— Make sure Flask-Migrate sees your models ———
    # This import registers User & QuizAttempt with SQLAlchemy before
    # Alembic autogenerates migrations.
    from . import models  

    # ——— Register blueprints ———
    app.register_blueprint(main)

    return app


if __name__ == '__main__':
    # Allows you to run `python -m myapp` for quick local tests
    create_app().run(debug=True)
