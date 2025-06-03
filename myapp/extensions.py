# myapp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

# This tells Flask-Login which endpoint to redirect to for logins.
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
