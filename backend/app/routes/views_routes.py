from flask import Blueprint, redirect, render_template, current_app, session, url_for
from ..models.user import User, AlumniProfile, StudentProfile
from ..models.user import Event, EventRegistration
from datetime import datetime
import os

views = Blueprint("views", __name__)

@views.route("/debug-paths")
def debug_paths():
    template_folder = current_app.template_folder
    template_path = os.path.join(current_app.root_path, template_folder)
    public_path = os.path.join(template_path, 'public')
    
    files_in_public = []
    if os.path.exists(public_path):
        files_in_public = os.listdir(public_path)
    
    return {
        'app_root_path': current_app.root_path,
        'template_folder': template_folder,
        'full_template_path': template_path,
        'public_folder_path': public_path,
        'public_folder_exists': os.path.exists(public_path),
        'files_in_public': files_in_public
    }
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@views.route("/alumni/profile")
def alumni_profile():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    alumni_profile = AlumniProfile.query.filter_by(user_id=user.id).first()
    
    return render_template("alumni/profile.html", 
                         user=user, 
                         profile=alumni_profile)


@views.route("/alumni/mentorship")
def alumni_mentorship():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    return render_template("alumni/mentorship.html", user=user)


@views.route("/")
def home():
    return render_template("public/home.html")

@views.route("/login")
def login_page():  
    return render_template("public/login.html")

@views.route("/register")
def register_page():
    return render_template("public/register.html")

@views.route("/alumni/dashboard")
def alumni_dashboard():
    try:
        user = get_current_user()
        if not user or user.role != 'alumni':
            return redirect(url_for('views.login_page'))
        
        print(f"Loading dashboard for user: {user.full_name}")

        from ..models.user import Conversation, Message
        unread_count = Message.query.join(Conversation).filter(
                Conversation.alumni_id == user.id,
                Message.is_read == False,
                Message.sender_id != user.id
            ).count()
        
        print(f"Unread count: {unread_count}")
        
        alumni_profile = AlumniProfile.query.filter_by(user_id=user.id).first()
        print(f"Alumni profile found: {alumni_profile is not None}")

        active_mentees_count = 8
        new_mentees = 2
        pending_requests = 4
        profile_views = 156
        weekly_views = 23
        recent_activities = [
                {
                    'icon': 'fa-user-graduate',
                    'title': 'New mentorship request from Michael Chen',
                    'description': 'Computer Science student • Interested in Software Engineering',
                    'time': '2 hours ago'
                },
                {
                    'icon': 'fa-comment',
                    'title': 'New message from Emily Rodriguez',
                    'description': 'Regarding career advice in Data Science',
                    'time': 'Yesterday'
                }
            ]
            
        return render_template("alumni/dashboard.html", 
                                user=user, 
                                profile=alumni_profile,
                                unread_count=unread_count,
                                active_mentees_count=active_mentees_count,
                                new_mentees=new_mentees,
                                pending_requests=pending_requests,
                                profile_views=profile_views,
                                weekly_views=weekly_views,
                                recent_activities=recent_activities)
    except Exception as e:
        print(f"ERROR in alumni_dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
    
@views.route("/alumni/test")
def alumni_test():
    user = get_current_user()
    return render_template("alumni/test.html", user=user)
    

@views.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin/dashboard.html")

@views.route("/alumni/messages")
def alumni_messages():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    
    from ..models.user import Conversation, Message
    unread_count = Message.query.join(Conversation).filter(
        Conversation.alumni_id == user.id,
        Message.is_read == False,
        Message.sender_id != user.id
    ).count()
    
    return render_template("alumni/messages.html", user=user, unread_count=unread_count)

@views.route("/alumni/students")
def browse_students():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
   
    from ..models.user import User, StudentProfile
    students = User.query.filter_by(role='student').all()
    
    student_list = []
    for student in students:
        profile = StudentProfile.query.filter_by(user_id=student.id).first()
        student_list.append({
            'id': student.id,
            'full_name': student.full_name,
            'email': student.email,
            'profile': profile
        })
    
    return render_template("alumni/students.html", 
                         user=user, 
                         students=student_list)




