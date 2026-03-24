from flask import Flask, render_template
from .config.db import app
from .routes.auth_routes import auth 
from .routes.profile_routes import profile_bp
from .routes.mentorship_routes import mentorship_bp
from .routes.chat_routes import chat_bp
from .routes.admin_routes import admin_bp
from .routes.payment_routes import payment_bp
from .routes.views_routes import views
from .routes.events_routes import events_bp
from .routes.student_routes import student_bp
from .routes.notification_routes import notification_bp
from .routes.notification_preferences_routes import preferences_bp
from .services.email_service import mail
from .routes.network_routes import network_bp

mail.init_app(app)

def register_blueprints():
    app.register_blueprint(views)
    app.register_blueprint(student_bp)
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(profile_bp)
    app.register_blueprint(mentorship_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(payment_bp, url_prefix="/api")
    app.register_blueprint(events_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(preferences_bp)
    app.register_blueprint(network_bp)

register_blueprints()
print("✓ Payment blueprint registered")

print("\n=== Registered Payment Routes ===")
for rule in app.url_map.iter_rules():
    if 'payment' in rule.endpoint:
        print(f"{rule.endpoint}: {rule}")