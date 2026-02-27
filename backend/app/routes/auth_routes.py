from flask import Blueprint, request, jsonify
from ..services.auth_service import create_user  


auth = Blueprint("auth", __name__)


@auth.route("/test")
def test():
    return jsonify({"message": "Auth routes working"})


@auth.route("/register", methods=["POST"])
def register():
    
    data = request.get_json()

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")  

    user, error = create_user(
        full_name,
        email,
        password,
        role
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "User registered successfully",
        "role": user.role
    }), 201