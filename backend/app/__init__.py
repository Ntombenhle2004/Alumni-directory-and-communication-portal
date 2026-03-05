from flask import Flask
from .config.db import app
from .routes.auth_routes import auth 
from .routes.profile_routes import profile_bp
from .routes.mentorship_routes import mentorship_bp
from .routes.chat_routes import chat_bp
from .routes.admin_routes import admin_bp
from .routes.payment_routes import payment_bp


def register_blueprints():
    
    
    @app.route("/")
    def home():
        return {
            "message": " API is running",
            "status": 200
        }


    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(mentorship_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(payment_bp, url_prefix='/api') 