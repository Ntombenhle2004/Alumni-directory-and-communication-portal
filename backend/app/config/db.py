import os
from urllib.parse import quote_plus
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

safe_password = quote_plus(password) if password else ""


SQLALCHEMY_DATABASE_URI = f"postgresql://{user}:{safe_password}@{host}:{port}/{db_name}"