from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from werkzeug.contrib.fixers import ProxyFix

# set up the Flask application
app = Flask(__name__)

app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
mail = Mail(app)

# login configuration
login_manager = LoginManager()
login_manager.init_app(app)

# load views
import app.views.user_management_views as user_management_views
import app.views.logged_in_views as logged_in_views
import app.views.group_views as group_views
login_manager.login_view = "login"


# configure app to be served by proxy
app.wsgi_app = ProxyFix(app.wsgi_app)

