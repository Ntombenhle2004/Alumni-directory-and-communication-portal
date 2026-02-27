import bcrypt
from ..config.db import db
from ..models.user import User


def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, hashed):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )


def create_user(full_name, email, password, role):


    if role == "admin":
        return None, "Admin cannot self register"

    existing = User.query.filter_by(email=email).first()

    if existing:
        return None, "User already exists"

    hashed_pw = hash_password(password)

    user = User(
        full_name=full_name,
        email=email,
        password_hash=hashed_pw,
        role=role
    )

    db.session.add(user)
    db.session.commit()

    return user, None