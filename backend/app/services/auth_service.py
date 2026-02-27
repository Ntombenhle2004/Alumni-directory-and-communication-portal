import bcrypt
from ..config.db import db
from ..models.user import User


def hash_password(password):
    """Hashes a plain text password for secure storage."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password, hashed):
    """Verifies a plain text password against the stored hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_user(full_name, email, password, role):
    """Standard registration for Students and Alumni."""
    if not all([full_name, email, password, role]):
        return None, "Error: full_name, email, password, and role are all required."

    if role.lower() == "admin":
        return None, "Security Error: Admin accounts cannot self-register. Use the admin creation endpoint."

    try:
        if User.query.filter_by(email=email).first():
            return None, f"Error: The email '{email}' is already registered."

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role.lower()
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database Error: {str(e)}"

def login_user(email, password):
    """Checks credentials and logs a user in."""
    if not email or not password:
        return None, "Error: Email and password are required."
    
    user = User.query.filter_by(email=email).first()
    if user and verify_password(password, user.password_hash):
        return user, None
    
    return None, "Login Failed: Invalid email or password."


def create_admin_by_admin(data):
    """Creates an admin. The ID is generated automatically by the database."""
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    if not all([email, password, full_name]):
        return None, "Error: Admin full_name, email, and password are required."

    if User.query.filter_by(email=email).first():
        return None, "Error: This email is already in use."

    try:
        new_admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role='admin'
        )
        db.session.add(new_admin)
        db.session.commit()
        return new_admin, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database Error: {str(e)}"

def get_all_users():
    return User.query.all()

def get_user_by_id(user_id):
    return User.query.get(user_id)

def update_user(user_id, data):
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "Error: User not found."

        if "full_name" in data: user.full_name = data["full_name"]
        if "email" in data: user.email = data["email"]
        if "password" in data: user.password_hash = hash_password(data["password"])
        
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def delete_user_by_id(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "Error: User not found."
        db.session.delete(user)
        db.session.commit()
        return True, "User deleted successfully."
    except Exception:
        db.session.rollback()
        return False, "Error: Could not delete user."