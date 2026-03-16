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
    
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    result = None
    error = None
    
    if user.role == 'student':
        result, error = profile_service.update_student_details(user.id, data)
    elif user.role == 'alumni':
        result, error = profile_service.update_alumni_details(user.id, data)
    else:
        error = "Invalid user role"
    
    if error:
        flash(error, 'error')
    else:
        flash('Profile updated successfully!', 'success')
    
    
    if request.is_json:
        if error:
            return jsonify({"error": error}), 400
        return jsonify({"message": "Profile updated successfully", "profile": result}), 200
    
    
    if user.role == 'student':
        return redirect(url_for('student.my_profile'))
    elif user.role == 'alumni':
        return redirect(url_for('views.alumni_profile'))
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
        # Add user ID to filename to avoid conflicts
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
    
    # Get profile data using service
    profile_data, error = profile_service.get_profile_logic(user.id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('student.dashboard'))
    
    return render_template("student/edit_profile.html", 
                         user=user, 
                         profile_data=profile_data)
