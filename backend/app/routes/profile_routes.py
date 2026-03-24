from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from ..services import profile_service
from ..models.user import User
from ..config.db import db
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint("profile_module", __name__, url_prefix="/profile")


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@profile_bp.route("/", methods=['GET'])
def get_profile():
    """Get the current user's profile (API endpoint)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    profile, error = profile_service.get_profile_logic(user_id)
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify(profile), 200

@profile_bp.route("/update", methods=['POST'])
def update_profile():
    """Update profile based on user role"""
    user = get_current_user()
    if not user:
        flash('Please login to update your profile.', 'error')
        return redirect(url_for('views.login_page'))
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Update user table fields first (full_name, email)
    if 'full_name' in data and data['full_name']:
        user.full_name = data['full_name']
    
    if 'email' in data and data['email']:
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user.id:
            flash('Email already in use by another account.', 'error')
            if user.role == 'student':
                return redirect(url_for('profile_module.student_profile_view'))
            else:
                return redirect(url_for('profile_module.alumni_profile_view'))
        user.email = data['email']
    
    # Handle profile picture upload
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Create unique filename
            unique_filename = f"user_{user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
            upload_dir = os.path.join('static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            user.profile_picture = unique_filename
    
    # Commit user changes
    db.session.commit()
    
    # Now update role-specific profile
    result = None
    error = None
    
    if user.role == 'student':
        # Prepare student-specific data
        student_data = {
            'course': data.get('course'),
            'graduation_year': data.get('graduation_year'),
            'interests': data.get('interests'),
            'is_subscribed': data.get('is_subscribed')
        }
        result, error = profile_service.update_student_details(user.id, student_data)
    elif user.role == 'alumni':
        # Prepare alumni-specific data
        alumni_data = {
            'job_title': data.get('job_title'),
            'company': data.get('company'),
            'industry': data.get('industry'),
            'skills': data.get('skills'),
            'graduation_year': data.get('graduation_year'),
            'mentorship_available': data.get('mentorship_available')
        }
        result, error = profile_service.update_alumni_details(user.id, alumni_data)
    else:
        error = "Invalid user role"
    
    if error:
        flash(error, 'error')
    else:
        flash('Profile updated successfully!', 'success')
    
    # Redirect based on user role
    if user.role == 'student':
        return redirect(url_for('profile_module.student_profile_view'))
    elif user.role == 'alumni':
        return redirect(url_for('profile_module.alumni_profile_view'))
    else:
        return redirect(url_for('views.home'))

@profile_bp.route("/picture", methods=['POST'])
def upload_picture():
    """Upload profile picture"""
    user = get_current_user()
    if not user:
        flash('Please login to upload a profile picture.', 'error')
        return redirect(url_for('views.login_page'))
    
    if 'profile_picture' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(request.referrer or url_for('profile_module.get_profile'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.referrer or url_for('profile_module.get_profile'))
    
    if file:
       
        filename = secure_filename(file.filename)
        
        filename = f"user_{user.id}_{filename}"
        
        
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
       
        file.save(os.path.join(upload_dir, filename))
        
     
        updated_user, error = profile_service.update_profile_pic(user.id, filename)
        
        if error:
            flash(error, 'error')
        else:
            flash('Profile picture updated successfully!', 'success')
    
    return redirect(request.referrer or url_for('views.home'))

@profile_bp.route("/student", methods=['GET'])
def student_profile_view():
    """Render student profile page"""
    user = get_current_user()
    if not user or user.role != 'student':
        flash('Please login as a student to view this page.', 'error')
        return redirect(url_for('views.login_page'))
    
    
    profile_data, error = profile_service.get_profile_logic(user.id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('student.dashboard'))
    
    return render_template("student/profile.html", 
                         user=user, 
                         profile_data=profile_data)

@profile_bp.route("/alumni", methods=['GET'])
def alumni_profile_view():
    """Render alumni profile page"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        flash('Please login as an alumni to view this page.', 'error')
        return redirect(url_for('views.login_page'))
    
   
    profile_data, error = profile_service.get_profile_logic(user.id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('views.alumni_dashboard'))
    
    return render_template("alumni/profile.html", 
                         user=user, 
                         profile_data=profile_data)

@profile_bp.route("/public/<int:user_id>", methods=['GET'])
def public_profile(user_id):
    """View public profile of any user"""
    current_user = get_current_user()
    
   
    profile_data, error = profile_service.get_profile_logic(user_id)
    
    if error:
        flash('User not found', 'error')
        return redirect(url_for('views.home'))
    
    
    if profile_data['role'] == 'student':
        template = "student/public_profile.html"
    elif profile_data['role'] == 'alumni':
        template = "alumni/public_profile.html"
    else:
        template = "public/profile.html"
    
    return render_template(template, 
                         profile=profile_data,
                         current_user=current_user)


@profile_bp.route("/student/edit", methods=['GET'])
def edit_alumni_profile():
    """Render student edit profile page"""
    user = get_current_user()
    if not user or user.role != 'student':
        flash('Please login as a student to view this page.', 'error')
        return redirect(url_for('views.login_page'))
    
    
    profile_data, error = profile_service.get_profile_logic(user.id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('student.dashboard'))
    
    return render_template("student/edit_profile.html", 
                         user=user, 
                         profile_data=profile_data)

@profile_bp.route("/student/edit", methods=['GET'])
def edit_student_profile():
    """Render student edit profile page"""
    user = get_current_user()
    if not user:
        flash('Please login to edit your profile.', 'error')
        return redirect(url_for('views.login_page'))
    
    if user.role != 'student':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('views.home'))
    
    
    profile_data, error = profile_service.get_profile_logic(user.id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('student.dashboard'))
    
    return render_template("student/edit_profile.html", 
                         user=user, 
                         profile_data=profile_data)

@profile_bp.route('/toggle-mentorship', methods=['POST'])
def toggle_mentorship():
    """Toggle mentorship availability for alumni"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    available = data.get('available', True)
    
    
    from ..models.user import AlumniProfile
    profile = AlumniProfile.query.filter_by(user_id=user.id).first()
    
    if not profile:
        profile = AlumniProfile(user_id=user.id)
        db.session.add(profile)
    
    profile.mentorship_available = available
    db.session.commit()
    
    status = "available" if available else "not available"
    return jsonify({
        'success': True,
        'message': f'You are now {status} for mentorship',
        'mentorship_available': profile.mentorship_available
    })

@profile_bp.route('/mentorship-status', methods=['GET'])
def get_mentorship_status():
    """Get current mentorship availability status"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return jsonify({'error': 'Unauthorized'}), 401
    
    from ..models.user import AlumniProfile
    profile = AlumniProfile.query.filter_by(user_id=user.id).first()
    
    return jsonify({
        'mentorship_available': profile.mentorship_available if profile else True
    })

@profile_bp.route("/alumni/settings", methods=['GET'])
def alumni_settings():
    """Render alumni settings page"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        flash('Please login as an alumni to view settings.', 'error')
        return redirect(url_for('views.login_page'))
    
    from ..models.user import AlumniProfile
    profile = AlumniProfile.query.filter_by(user_id=user.id).first()
    
    return render_template("alumni/settings.html", 
                         user=user, 
                         profile=profile)

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

        # Update fields only if they are provided
        if 'job_title' in data and data['job_title']:
            profile.job_title = data['job_title']
        if 'company' in data and data['company']:
            profile.company = data['company']
        if 'industry' in data and data['industry']:
            profile.industry = data['industry']
        if 'skills' in data and data['skills']:
            profile.skills = data['skills']
        if 'graduation_year' in data and data['graduation_year']:
            try:
                profile.graduation_year = int(data['graduation_year'])
            except (ValueError, TypeError):
                pass
        
        # Handle mentorship_available checkbox
        if 'mentorship_available' in data:
            val = data['mentorship_available']
            if isinstance(val, str):
                profile.mentorship_available = val.lower() == 'true' or val == 'on'
            else:
                profile.mentorship_available = bool(val)
        
        db.session.commit()
        return profile, None
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return None, f"Alumni update failed: {str(e)}"