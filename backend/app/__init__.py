from flask import Flask
from dotenv import load_dotenv
import os
from .config.db import db

# ✅ ADD THIS LINE
from .routes.auth_routes import auth

load_dotenv()

def create_app():

    app = Flask(__name__)

    # Database config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # ✅ Register routes AFTER import
    app.register_blueprint(auth)

    from .models.user import User

    return app