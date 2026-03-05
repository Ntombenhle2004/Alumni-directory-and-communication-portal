from ..models.user import User, AlumniProfile, MentorshipRequest
from ..config.db import db
# from .notification_service import send_notification

def send_request_logic(data):
    try:
        student_id = data.get("student_id")
        alumni_id = data.get("alumni_id")
        
        alumni_profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()
        if not alumni_profile:
            return None, "Alumnus profile not found."
        
        if not alumni_profile.mentorship_available:
            return None, "This mentor is currently not accepting new requests."

        existing = MentorshipRequest.query.filter_by(
            student_id=student_id, 
            alumni_id=alumni_id, 
            status='Pending'
        ).first()
        if existing:
            return None, "You already have a pending request for this mentor."

        new_request = MentorshipRequest(
            student_id=student_id, 
            alumni_id=alumni_id,
            status='Pending'
        )
        db.session.add(new_request)
        db.session.commit()


        # send_notification(
        #     alumni_id, 
        #     f" You have a new mentorship request from Student ID {student_id}!", 
        #     "mentorship"
        # )

        return new_request, None

    except Exception as e:
        db.session.rollback()
        return None, str(e)

def update_request_status(request_id, status):
    """Updates status and notifies student ONLY if accepted."""
    try:
        req = MentorshipRequest.query.get(request_id)
        if not req:
            return None, "Request not found."

        if status not in ['Accepted', 'Rejected']:
            return None, "Invalid status. Use 'Accepted' or 'Rejected'."

        req.status = status
        db.session.commit()

    
        # if status == 'Accepted':
        #     send_notification(
        #         req.student_id, 
        #         f"Your mentorship request to Mentor ID {req.alumni_id} has been ACCEPTED!", 
        #         "mentorship"
        #     )
        
        return req, None
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