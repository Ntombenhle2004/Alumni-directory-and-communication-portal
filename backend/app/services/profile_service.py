from ..models.user import User, StudentProfile, AlumniProfile
from ..config.db import db
from datetime import datetime

def get_profile_logic(user_id):
    """
    Fetches full user info plus their specific role-based details.
    Used for the main Dashboard view.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "User not found."

        profile_data = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "profile_picture": user.profile_picture,
            "created_at": user.created_at.strftime("%Y-%m-%d")
        }

        role = user.role.lower()

        if role == 'student':
            p = StudentProfile.query.filter_by(user_id=user.id).first()
            profile_data["details"] = {
                "course": p.course if p else None,
                "graduation_year": p.graduation_year if p else None,
                "interests": p.interests if p else None,
                "is_subscribed": p.is_subscribed if p else False
            }
        elif role in ['alumni', 'alumn']:
            p = AlumniProfile.query.filter_by(user_id=user.id).first()
            profile_data["details"] = {
                "job_title": p.job_title if p else None,
                "company": p.company if p else None,
                "industry": p.industry if p else None,
                "skills": p.skills if p else None,
                "mentorship_available": p.mentorship_available if p else True
            }
        else:
            profile_data["details"] = {}

        return profile_data, None
    except Exception as e:
        return None, f"Error fetching profile: {str(e)}"

def update_student_details(user_id, data):
    """Updates Student table. Creates the row if it's the first time."""
    try:
        user = User.query.get(user_id)
        if not user or user.role.lower() != 'student':
            return None, "Unauthorized: User is not a student."

        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = StudentProfile(user_id=user_id)
            db.session.add(profile)

        if 'course' in data:
            profile.course = data['course']
        if 'graduation_year' in data and data['graduation_year']:
            profile.graduation_year = int(data['graduation_year'])
        if 'interests' in data:
            profile.interests = data['interests']
        
        # Fix: Convert string 'true'/'false' to boolean
        if 'is_subscribed' in data:
            val = data['is_subscribed']
            if isinstance(val, str):
                profile.is_subscribed = val.lower() == 'true'
            else:
                profile.is_subscribed = bool(val)
        
        db.session.commit()
        return profile, None
    except Exception as e:
        db.session.rollback()
        return None, f"Student update failed: {str(e)}"

def update_alumni_details(user_id, data):
    """Updates Alumni table. Handles 'alumni' or 'alumn' roles."""
    try:
        user = User.query.get(user_id)
        
        if not user or user.role.lower() not in ['alumni', 'alumn']:
            return None, f"Unauthorized: User is a {user.role if user else 'None'}, not an alumnus."

        profile = AlumniProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = AlumniProfile(user_id=user_id)
            db.session.add(profile)

        if 'job_title' in data:
            profile.job_title = data['job_title']
        if 'company' in data:
            profile.company = data['company']
        if 'industry' in data:
            profile.industry = data['industry']
        if 'skills' in data:
            profile.skills = data['skills']
        if 'graduation_year' in data and data['graduation_year']:
            profile.graduation_year = int(data['graduation_year'])
        
        
        if 'mentorship_available' in data:
            val = data['mentorship_available']
            if isinstance(val, str):
                profile.mentorship_available = val.lower() == 'true'
            else:
                profile.mentorship_available = bool(val)
        
        db.session.commit()
        return profile, None
    except Exception as e:
        db.session.rollback()
        return None, f"Alumni update failed: {str(e)}"

def update_profile_pic(user_id, filename):
    """Updates the user's avatar filename."""
    try:
        user = User.query.get(user_id)
        if not user:
            return None, "User not found."
            
        user.profile_picture = filename
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, f"Picture update failed: {str(e)}"