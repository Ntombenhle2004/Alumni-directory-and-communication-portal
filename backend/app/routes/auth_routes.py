from flask import Blueprint, request, jsonify, render_template, redirect, session, url_for, flash  
from ..config.db import db
from ..models.user import User, StudentProfile, AlumniProfile
from ..services import auth_service  # This is correct based on your file structure
import re

auth = Blueprint("auth", __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        print("GET request to /auth/register - redirecting to register page")
        return redirect(url_for('views.register_page'))
    
    print("="*50)
    print("POST request to /auth/register received")
    print(f"Request content type: {request.content_type}")
    print(f"Form data: {request.form}")
    
    
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    role = data.get('role', 'student')

    print(f"Registration attempt: full_name='{full_name}', email='{email}', role='{role}'")
    print(f"Password length: {len(password) if password else 0}, Confirm password length: {len(confirm_password) if confirm_password else 0}")
    

    if not all([full_name, email, password, confirm_password]):
        error = "All fields are required"
        if request.is_json:
            return jsonify({"error": error}), 400
        return render_template("public/register.html", error=error)
    
    
    if password != confirm_password:
        error = "Passwords do not match"
        if request.is_json:
            return jsonify({"error": error}), 400
        return render_template("public/register.html", error=error)
    
    
    new_user, error = auth_service.create_user(full_name, email, password, role)
    
    if error:
        if request.is_json:
            return jsonify({"error": error}), 400
        return render_template("public/register.html", error=error)
    
    try:
        if role == 'student':
            profile = StudentProfile(
                user_id=new_user.id,
                course=data.get('course', ''),
                graduation_year=data.get('graduation_year', None) if data.get('graduation_year') else None,
                interests=data.get('interests', '')
            )
            db.session.add(profile)
        elif role == 'alumni':
            profile = AlumniProfile(
                user_id=new_user.id,
                job_title=data.get('job_title', ''),
                company=data.get('company', ''),
                industry=data.get('industry', ''),
                skills=data.get('skills', ''),
                graduation_year=data.get('graduation_year', None) if data.get('graduation_year') else None
            )
            db.session.add(profile)
        
        db.session.commit()
        print("Profile created and committed successfully")
    except Exception as e:
        db.session.rollback()

        db.session.delete(new_user)
        db.session.commit()
        error = f"Error creating profile: {str(e)}"
        if request.is_json:
            return jsonify({"error": error}), 400
        return render_template("public/register.html", error=error)
    
    print("Registration successful! Redirecting to login page")
    flash("Registration successful! Please login.", "success")
    return redirect(url_for('views.login_page'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        print("GET request to /auth/login - redirecting to login page")
        return redirect(url_for('views.login_page'))
    
    print("POST request to /auth/login received")
    print(f"Form data: {request.form}")
    

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    email = data.get('email')
    password = data.get('password')
    
    print(f"Login attempt for email: {email}")
    
    if not email or not password:
        error = "Email and password are required"
        print(f"Validation error: {error}")
        flash(error, "error")
        return render_template("public/login.html", error=error)
    
    
    user, error = auth_service.login_user(email, password)
    
    if error or not user:
        error = error or "Invalid email or password"
        print(f"Login failed: {error}")
        flash(error, "error")
        return render_template("public/login.html", error=error)
    
    print(f"Login successful for user: {user.full_name} (ID: {user.id}, Role: {user.role})")
    

    from flask import session
    session['user_id'] = user.id
    session['user_role'] = user.role
    session['user_name'] = user.full_name
    
    flash(f"Welcome back, {user.full_name}!", "success")
    
    
    if user and auth_service.verify_password(password, user.password_hash):
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['user_role'] = user.role
        
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'alumni':
            return redirect(url_for('views.alumni_dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    


@auth.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('views.home'))