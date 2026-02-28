# from flask import Blueprint, request, jsonify
# from ..services.auth_service import (
#     create_user, login_user, get_all_users, get_user_by_id, 
#     update_user, delete_user_by_id, create_admin_by_admin
# )

# auth = Blueprint("auth", __name__)

# @auth.route("/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     user, error = login_user(data.get("email"), data.get("password"))
#     if error: return jsonify({"error": error}), 401
#     return jsonify({
#         "message": f"Welcome back, {user.full_name}",
#         "id": user.id,
#         "role": user.role
#     }), 200

# @auth.route("/register", methods=["POST"])
# def register():
#     data = request.get_json()
#     user, error = create_user(
#         data.get("full_name"), 
#         data.get("email"), 
#         data.get("password"), 
#         data.get("role")
#     )
#     if error: return jsonify({"error": error}), 400
#     return jsonify({"message": "User registered successfully", "user_id": user.id}), 201

# @auth.route("/admin/create", methods=["POST"])
# def admin_create():
#     data = request.get_json()
#     new_admin, error = create_admin_by_admin(data)
#     if error: return jsonify({"error": error}), 400
#     return jsonify({"message": "Admin created", "assigned_id": new_admin.id}), 201

# @auth.route("/users", methods=["GET"])
# def view_all():
#     users = get_all_users()
#     # Changed 'name' to 'full_name' in the response
#     return jsonify([{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role} for u in users]), 200

# @auth.route("/users/<int:id>", methods=["GET", "PUT", "DELETE"])
# def user_ops(id):
#     if request.method == "GET":
#         user = get_user_by_id(id)
#         if not user: return jsonify({"error": "User not found"}), 404
#         return jsonify({"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}), 200
    
#     if request.method == "PUT":
#         # Pass the whole JSON body to the update service
#         user, error = update_user(id, request.get_json())
#         if error: return jsonify({"error": error}), 400
#         return jsonify({"message": "User updated successfully"}), 200
    
#     if request.method == "DELETE":
#         success, message = delete_user_by_id(id)
#         if not success: return jsonify({"error": message}), 404
#         return jsonify({"message": message}), 200





from flask import Blueprint, request, jsonify
from ..services.auth_service import (
    create_user, login_user, get_all_users, get_user_by_id, 
    update_user, delete_user_by_id, create_admin_by_admin
)

auth = Blueprint("auth", __name__)

# --- LOGIN WITH DASHBOARD ROUTING ---

@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user, error = login_user(data.get("email"), data.get("password"))
    
    if error: 
        return jsonify({"error": error}), 401

    # Logic to determine which dashboard the user should see
    role = user.role.lower()
    if role == "admin":
        dashboard_url = "/admin/dashboard"
    elif role == "student":
        dashboard_url = "/student/dashboard"
    elif role == "alumni":
        dashboard_url = "/alumni/dashboard"
    else:
        dashboard_url = "/home"

    return jsonify({
        "message": f"Welcome back, {user.full_name}",
        "user_data": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "profile_picture": user.profile_picture # Added for your UI
        },
        "redirect_to": dashboard_url
    }), 200

# --- REGISTRATION ---

@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    user, error = create_user(
        data.get("full_name"), 
        data.get("email"), 
        data.get("password"), 
        data.get("role")
    )
    if error: return jsonify({"error": error}), 400
    return jsonify({"message": "User registered successfully", "user_id": user.id}), 201

# --- ADMIN CREATION ---

@auth.route("/admin/create", methods=["POST"])
def admin_create():
    data = request.get_json()
    new_admin, error = create_admin_by_admin(data)
    if error: return jsonify({"error": error}), 400
    return jsonify({"message": "Admin created", "assigned_id": new_admin.id}), 201

# --- USER MANAGEMENT (VIEW ALL) ---

@auth.route("/users", methods=["GET"])
def view_all():
    users = get_all_users()
    return jsonify([{
        "id": u.id, 
        "full_name": u.full_name, 
        "email": u.email, 
        "role": u.role,
        "profile_picture": u.profile_picture
    } for u in users]), 200

# --- USER OPERATIONS (GET ONE, UPDATE, DELETE) ---

@auth.route("/users/<int:id>", methods=["GET", "PUT", "DELETE"])
def user_ops(id):
    if request.method == "GET":
        user = get_user_by_id(id)
        if not user: return jsonify({"error": "User not found"}), 404
        return jsonify({
            "id": user.id, 
            "full_name": user.full_name, 
            "email": user.email, 
            "role": user.role,
            "profile_picture": user.profile_picture
        }), 200
    
    if request.method == "PUT":
        # Supports updating full_name, email, role, and password
        user, error = update_user(id, request.get_json())
        if error: return jsonify({"error": error}), 400
        return jsonify({"message": "User updated successfully"}), 200
    
    if request.method == "DELETE":
        success, message = delete_user_by_id(id)
        if not success: return jsonify({"error": message}), 404
        return jsonify({"message": message}), 200