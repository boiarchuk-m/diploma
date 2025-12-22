from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_login import LoginManager

load_dotenv()
login_manager = LoginManager()

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "photos")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB, наприклад

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)



login_manager.init_app(app)
login_manager.login_view = 'login'

from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    # Return the user object for the given user_id
    return User.query.get(int(user_id))

from app.routes import test
from app.routes.admin import admin_bp
from app.routes.onboarding import onboarding_bp
from app.routes.profile import profile_bp
from app.routes.saved_offers import saved_offers_bp
from app.routes.auth import auth_bp
from app.routes.offers import offers_bp


app.register_blueprint(admin_bp)
app.register_blueprint(onboarding_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(saved_offers_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(offers_bp)

