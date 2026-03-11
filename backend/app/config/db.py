import os
from urllib.parse import quote_plus
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(backend_dir, 'templates')



app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))



SQLALCHEMY_DATABASE_URI = f"sqlite:///alumni_portal.db"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SECRET_KEY"] = "your-secret-key-here-change-this-in-production"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)



