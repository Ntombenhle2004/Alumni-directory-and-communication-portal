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
    print(f"[auth_service] Creating user: {full_name}, {email}, role={role}")
    
    if not all([full_name, email, password, role]):
        print("[auth_service] Missing required fields")
        return None, "Error: full_name, email, password, and role are all required."

    if role.lower() == "admin":
        print("[auth_service] Admin self-registration attempted")
        return None, "Security Error: Admins cannot self-register."

    try:
       
        print(f"[auth_service] Checking if email {email} already exists")
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"[auth_service] Email {email} already registered")
            return None, "Error: Email already registered."

        
        print("[auth_service] Hashing password...")
        hashed_password = hash_password(password)
        print(f"[auth_service] Password hashed successfully: {hashed_password[:30]}...")
        

        print("[auth_service] Creating user object...")
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role=role.lower()
        )
        db.session.add(new_user)
        print("[auth_service] Committing user to database...")
        db.session.commit()
        print(f"[auth_service] User created with ID: {new_user.id}")
        
        return new_user, None
        
    except Exception as e:
        db.session.rollback()
        print(f"[auth_service] ERROR creating user: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, str(e)

def login_user(email, password):
    """Verifies credentials and returns user info for dashboard routing."""
    if not email or not password:
        return None, "Email and password are required."
    
    user = User.query.filter_by(email=email).first()
    
    if user and verify_password(password, user.password_hash):
        return user, None
    
    return None, "Invalid email or password."

def create_admin_by_admin(data):
    """Allows an existing admin to create another admin."""
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    if not all([email, password, full_name]):
        return None, "Error: full_name, email, and password are required."

    try:
        if User.query.filter_by(email=email).first():
            return None, "Error: Email already in use."

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
        return None, str(e)


def get_all_users():
    """Returns all users in the database."""
    return User.query.all()

def get_user_by_id(user_id):
    """Returns a specific user by their ID."""
    return User.query.get(user_id)

def update_user(user_id, data):
    """Updates user details including name, email, and hashed password."""
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "User not found."
        if "full_name" in data:
            user.full_name = data["full_name"]

        if "email" in data:
            existing = User.query.filter_by(email=data["email"]).first()
            if existing and existing.id != user_id:
                return None, "Email already in use."
            user.email = data["email"]

        if "role" in data:
            user.role = data["role"].lower()

        if "password" in data and data["password"]:
            user.password_hash = hash_password(data["password"])

        db.session.commit()
        db.session.refresh(user)
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def delete_user_by_id(user_id):
    """Removes a user from the database."""
    try:
        user = User.query.get(user_id)
        if not user: 
            return False, "User not found."
        
        db.session.delete(user)
        db.session.commit()
        return True, "Deleted successfully."
    except Exception:
        db.session.rollback()
        return False, "Delete failed."