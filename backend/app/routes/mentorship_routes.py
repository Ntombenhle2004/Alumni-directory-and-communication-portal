from flask import Blueprint, request, jsonify
from ..services.mentorship_service import (
    send_request_logic, get_requests_by_role, update_request_status
)

mentorship_bp = Blueprint("mentorship", __name__)

@mentorship_bp.route("/mentorship/request", methods=["POST"])
def request_mentorship():
    data = request.get_json()
    req, error = send_request_logic(data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Request sent successfully", "id": req.id}), 201

@mentorship_bp.route("/mentorship/my-requests/<int:user_id>/<string:role>", methods=["GET"])
def view_requests(user_id, role):
    requests, error = get_requests_by_role(user_id, role)
    if error:
        return jsonify({"error": error}), 400
    
    output = []
    for r in requests:
        output.append({
            "request_id": r.id,
            "student_id": r.student_id,
            "alumni_id": r.alumni_id,
            "status": r.status,
            "date": r.request_date.strftime("%Y-%m-%d")
        })
    return jsonify(output), 200

@mentorship_bp.route("/mentorship/respond/<int:request_id>", methods=["PUT"])
def respond_to_request(request_id):
    data = request.get_json()
    status = data.get("status") # 'Accepted' or 'Rejected'
    
    req, error = update_request_status(request_id, status)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": f"Request {status} successfully"}), 200