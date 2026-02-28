from flask import Blueprint, request, jsonify
from ..services.profile_service import (
    get_profile_logic, update_student_details, 
    update_alumni_details, update_profile_pic
)

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    """
    Fetches the combined User + Role-specific profile.
    This is what you call when the dashboard loads.
    """
    data, error = get_profile_logic(user_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(data), 200


@profile_bp.route("/profile/student/<int:user_id>", methods=["PUT"])
def edit_student(user_id):
    """Updates course, graduation, and interests for a student."""
    data = request.get_json()
   
    profile, error = update_student_details(user_id, data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Student profile updated successfully"}), 200

@profile_bp.route("/profile/alumni/<int:user_id>", methods=["PUT"])
def edit_alumni(user_id):
    """
    Updates job title, company, industry, skills, and mentorship availability.
    Example JSON: {"company": "Google", "mentorship_available": false}
    """
    data = request.get_json()
    profile, error = update_alumni_details(user_id, data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Alumni profile updated successfully"}), 200


@profile_bp.route("/profile/picture/<int:user_id>", methods=["PUT"])
def edit_picture(user_id):
    """Updates the filename of the profile picture in the users table."""
    data = request.get_json()
    filename = data.get("profile_picture")
    
    if not filename:
        return jsonify({"error": "No profile_picture filename provided"}), 400
    
    user, error = update_profile_pic(user_id, filename)
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify({
        "message": "Profile picture updated", 
        "filename": user.profile_picture
    }), 200