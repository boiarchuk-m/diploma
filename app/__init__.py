from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
#from flask_login import LoginManager

load_dotenv()

#login_manager = LoginManager()
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


#login_manager.init_app(app)
#login_manager.login_view = 'login'

from app.test import test


app.register_blueprint(test)
