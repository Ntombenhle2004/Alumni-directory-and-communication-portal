
from flask import Flask
from .config.db import db, SQLALCHEMY_DATABASE_URI
from dotenv import load_dotenv

load_dotenv()


from .routes.auth_routes import auth

def create_app():
    app = Flask(__name__)

   
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

 
    app.register_blueprint(auth, url_prefix="/auth")

  
    @app.route("/")
    def home():
        return "Flask Backend is Running"

    print("App created and blueprint registered")  

    return app