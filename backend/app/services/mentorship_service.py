from ..models.user import User, AlumniProfile, MentorshipRequest
from ..config.db import db

def send_request_logic(data):
    try:
        student_id = data.get("student_id")
        alumni_id = data.get("alumni_id")
        message = data.get("message", "I would like you to be my mentor.")

        # 1. Check if Alumni exists and is available
        alumni_profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()
        if not alumni_profile:
            return None, "Alumnus profile not found."
        
        if not alumni_profile.mentorship_available:
            return None, "This mentor is currently not accepting new requests."

        # 2. Prevent duplicate pending requests
        existing = MentorshipRequest.query.filter_by(
            student_id=student_id, 
            alumni_id=alumni_id, 
            status='Pending'
        ).first()
        if existing:
            return None, "You already have a pending request for this mentor."

        # 3. Create the request
        new_request = MentorshipRequest(
            student_id=student_id, 
            alumni_id=alumni_id,
            status='Pending'
        )
        db.session.add(new_request)
        db.session.commit()
        return new_request, None

    except Exception as e:
        db.session.rollback()
        return None, str(e)

def get_requests_by_role(user_id, role):
    """Fetches requests based on whether the user is a student or alumni."""
    try:
        if role.lower() == 'student':
            return MentorshipRequest.query.filter_by(student_id=user_id).all(), None
        else:
            return MentorshipRequest.query.filter_by(alumni_id=user_id).all(), None
    except Exception as e:
        return None, str(e)

def update_request_status(request_id, status):
    """Updates status to 'Accepted' or 'Rejected'."""
    try:
        req = MentorshipRequest.query.get(request_id)
        if not req:
            return None, "Request not found."

        if status not in ['Accepted', 'Rejected']:
            return None, "Invalid status. Use 'Accepted' or 'Rejected'."

        req.status = status
        db.session.commit()
        return req, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)