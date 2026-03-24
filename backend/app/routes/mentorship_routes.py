from flask import Blueprint, request, jsonify, session, redirect, url_for
from ..models.user import User, MentorshipRequest, AlumniProfile
from ..services.notification_service import NotificationService
from ..services.email_service import send_mentorship_request_email, send_mentorship_response_email  # Fixed import
from ..config.db import db
from datetime import datetime

mentorship_bp = Blueprint("mentorship", __name__)

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@mentorship_bp.route("/mentorship/request/<int:alumni_id>", methods=["POST"])
def request_mentorship(alumni_id):
    """Student sends a mentorship request directly."""
    student = get_current_user()
    if not student or student.role != 'student':
        return jsonify({"error": "Unauthorized"}), 401

    alumni = User.query.get(alumni_id)
    if not alumni or alumni.role != 'alumni':
        return jsonify({"error": "Alumni not found"}), 404

    alumni_profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()
    if not alumni_profile or not alumni_profile.mentorship_available:
        return jsonify({"error": "This alumni is not available for mentorship"}), 400

    existing = MentorshipRequest.query.filter_by(
        student_id=student.id,
        alumni_id=alumni_id
    ).first()
    if existing:
        return jsonify({"error": f"Mentorship request already {existing.status}"}), 400

    data = request.get_json() or {}
    message = data.get('message', '')

    mentorship_request = MentorshipRequest(
        student_id=student.id,
        alumni_id=alumni_id,
        message=message,
        status='pending',
        payment_status='unpaid'
    )
    db.session.add(mentorship_request)
    db.session.commit()

    # Create in-app notification
    NotificationService.create_notification(
        user_id=alumni_id,
        sender_id=student.id,
        title="New Mentorship Request",
        message=f"{student.full_name} has requested you as a mentor.",
        notification_type='mentorship_request',
        reference_id=mentorship_request.id,
        reference_type='mentorship'
    )
    
    # Send email notification to alumni
    send_mentorship_request_email(student, alumni, mentorship_request)

    return jsonify({
        'success': True,
        'message': 'Mentorship request sent successfully',
        'request_id': mentorship_request.id
    }), 201

@mentorship_bp.route("/respond/<int:request_id>", methods=["POST"])
def respond_to_request(request_id):
    """Alumni accepts/rejects the mentorship request."""
    alumni = get_current_user()
    if not alumni or alumni.role != 'alumni':
        return jsonify({"error": "Unauthorized"}), 401

    req = MentorshipRequest.query.get_or_404(request_id)
    if req.alumni_id != alumni.id:
        return jsonify({"error": "Not authorized"}), 403

    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        action = data.get('action')
        response_message = data.get('response_message', '')
    else:
        # Handle form data from HTML form
        action = request.form.get('action')
        response_message = request.form.get('response_message', '')
    
    print(f"Action received: {action}")  # Debug print
    
    if action not in ['accept', 'reject']:
        return jsonify({"error": "Invalid action"}), 400

    # Get student for email
    student = User.query.get(req.student_id)
    
    if action == 'accept':
        req.status = 'accepted'
        req.payment_status = 'unpaid'
    else:
        req.status = 'rejected'

    req.response_date = datetime.utcnow()
    req.response_message = response_message
    db.session.commit()

    # Send in-app notification
    status_text = 'accepted' if action == 'accept' else 'declined'
    NotificationService.create_notification(
        user_id=req.student_id,
        sender_id=alumni.id,
        title=f"Mentorship Request {status_text.title()}",
        message=f"{alumni.full_name} has {status_text} your mentorship request.",
        notification_type='mentorship_response',
        reference_id=req.id,
        reference_type='mentorship'
    )
    
    # Send email notification to student
    from ..services.email_service import send_mentorship_response_email
    send_mentorship_response_email(student, alumni, req, action)

    # For API requests, return JSON
    if request.is_json:
        return jsonify({
            'success': True,
            'message': f'Request {action}ed successfully'
        }), 200
    
    # For form submissions, redirect back to mentorship page
    return redirect(url_for('views.alumni_mentorship'))