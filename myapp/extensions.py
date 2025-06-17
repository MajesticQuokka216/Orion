# myapp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login     import LoginManager
from flask_bcrypt    import Bcrypt
from flask_migrate   import Migrate

db            = SQLAlchemy()
login_manager = LoginManager()
bcrypt        = Bcrypt()
migrate       = Migrate()

login_manager.login_view        = 'main.login'
login_manager.login_message_cat = 'info'
