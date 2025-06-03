# myapp/__init__.py
from flask import Flask
from .extensions import db, login_manager, bcrypt
from .routes import main

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints (we created a blueprint called "main")
    app.register_blueprint(main)

    return app
