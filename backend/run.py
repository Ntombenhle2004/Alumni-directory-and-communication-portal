from app import register_blueprints
from app.config.db import db, app

# blueprints = register_blueprints()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)