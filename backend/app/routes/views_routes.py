from flask import Blueprint, flash, jsonify, redirect, render_template, current_app, request, session, url_for

from ..config.db import db
from ..models.user import MentorshipSession, User, AlumniProfile, StudentProfile, MentorshipRequest
from ..models.user import Event, EventRegistration
from ..models.user import Notification
from ..models.user import Conversation, Message
from ..models.user import Conversation
from ..models.user import Conversation

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
    
    # Get profile data using service
    from ..services import profile_service
    profile_data, error = profile_service.get_profile_logic(user.id)
    
    if error:
        flash(error, 'error')
        return redirect(url_for('views.alumni_dashboard'))
    
    return render_template("alumni/profile.html", 
                         user=user, 
                         profile_data=profile_data)  # Make sure this is passedssed


@views.route("/alumni/mentorship")
def alumni_mentorship():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipRequest, User
    
    
    pending_requests = MentorshipRequest.query.filter_by(
        alumni_id=user.id,
        status='pending'
    ).order_by(MentorshipRequest.request_date.desc()).all()
    
   
    active_mentees = MentorshipRequest.query.filter_by(
        alumni_id=user.id,
        status='accepted'
    ).order_by(MentorshipRequest.request_date.desc()).all()
    
    
    for request in pending_requests:
        student = User.query.get(request.student_id)
        request.student_name = student.full_name if student else "Unknown Student"
    
    for mentee in active_mentees:
        student = User.query.get(mentee.student_id)
        mentee.student_name = student.full_name if student else "Unknown Student"
    
    upcoming_sessions = []
    for mentee in active_mentees:
        sessions = MentorshipSession.query.filter_by(
            mentorship_request_id=mentee.id,
            status='scheduled'
        ).filter(MentorshipSession.session_date >= datetime.utcnow()).order_by(MentorshipSession.session_date.asc()).all()

        for session in sessions:
            student = User.query.get(mentee.student_id)
            upcoming_sessions.append({
                'id': session.id,
                'title': session.title,
                'session_date': session.session_date,
                'duration_minutes': session.duration_minutes,
                'meeting_platform': session.meeting_platform,
                'meeting_link': session.meeting_link,
                'mentee_name': student.full_name if student else 'Student'
            })
    
    alumni_profile = AlumniProfile.query.filter_by(user_id=user.id).first()
    
    return render_template("alumni/mentorship.html", 
                         user=user,
                         pending_requests=pending_requests,

                         upcoming_sessions = upcoming_sessions,
                         active_mentees=active_mentees,
                         profile=alumni_profile,)


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
@views.route("/alumni/dashboard")
def alumni_dashboard():
    try:
        user = get_current_user()
        if not user or user.role != 'alumni':
            return redirect(url_for('views.login_page'))


        unread_notifications_count = Notification.query.filter_by(
            user_id=user.id,
            is_read=False
        ).count()

        from ..models.user import Conversation, Message, MentorshipRequest, AlumniProfile, StudentProfile, User
        
        
        unread_count = Message.query.join(Conversation).filter(
            Conversation.alumni_id == user.id,
            Message.is_read == False,
            Message.sender_id != user.id
        ).count()
        
        
        pending_requests = MentorshipRequest.query.filter_by(
            alumni_id=user.id,
            status='pending'
        ).order_by(MentorshipRequest.request_date.desc()).all()
        
       
        active_mentees_count = MentorshipRequest.query.filter_by(
            alumni_id=user.id,
            status='accepted'
        ).count()
        
      
        for request in pending_requests:
            student = User.query.get(request.student_id)
            if student:
                request.student_name = student.full_name
                
                student_profile = StudentProfile.query.filter_by(user_id=student.id).first()
                request.student_course = student_profile.course if student_profile else None
                request.student_id = student.id  
        
        print(f"Unread count: {unread_count}")
        print(f"Pending requests: {len(pending_requests)}")
        
       
        alumni_profile = AlumniProfile.query.filter_by(user_id=user.id).first()
        print(f"Alumni profile found: {alumni_profile is not None}")
        
      
        if alumni_profile and alumni_profile.rating_count and alumni_profile.rating_count > 0:
            from ..models.user import Rating
            ratings = Rating.query.filter_by(alumni_id=user.id).all()
            avg_rating = sum(r.score for r in ratings) / len(ratings) if ratings else 0
            alumni_profile.rating_avg = avg_rating
        
   
        recent_activities = []
        
       
        for req in pending_requests[:3]:  
            recent_activities.append({
                'icon': 'fa-clock',
                'title': f'New mentorship request from {req.student_name if hasattr(req, "student_name") else "a student"}',
                'description': req.message[:50] + '...' if req.message and len(req.message) > 50 else (req.message or 'No message provided'),
                'time': req.request_date.strftime('%b %d, %Y') if req.request_date else 'Recently',
                'type': 'request'
            })
        
        
        if not recent_activities:
            recent_activities = [
                {
                    'icon': 'fa-bell',
                    'title': 'No recent activity',
                    'description': 'Your dashboard is quiet. Check back later for updates.',
                    'time': 'Now'
                }
            ]
        
       
        profile_views = 7  
        weekly_views = 23    
        new_mentees = 2      
        
        return render_template("alumni/dashboard.html", 
                             user=user, 
                             profile=alumni_profile,
                            unread_notifications_count=unread_notifications_count,
                             unread_count=unread_count,
                             active_mentees_count=active_mentees_count,
                             new_mentees=new_mentees,
                             pending_requests=pending_requests,
                             pending_requests_count=len(pending_requests),
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
    """Show all conversations for alumni"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Conversation, Message, User
    
    conversations = Conversation.query.filter(
        (Conversation.student_id == user.id) | (Conversation.alumni_id == user.id)
    ).order_by(Conversation.created_at.desc()).all()
    
    conversation_list = []
    for conv in conversations:
        # Determine the other user
        other_id = conv.alumni_id if conv.student_id == user.id else conv.student_id
        other_user = User.query.get(other_id)
        
        if not other_user:
            continue
        
        # Get last message
        last_message = Message.query.filter_by(conversation_id=conv.id).order_by(Message.sent_at.desc()).first()
        
        # Get unread count
        unread_count = Message.query.filter_by(
            conversation_id=conv.id,
            is_read=False
        ).filter(Message.sender_id != user.id).count()
        
        conversation_list.append({
            'id': conv.id,
            'other_user_id': other_id,
            'other_user_name': other_user.full_name,
            'other_user_avatar': other_user.full_name[:2].upper(),
            'other_user_role': other_user.role,
            'last_message': last_message.message if last_message else "No messages yet",
            'last_message_time': last_message.sent_at.strftime('%b %d, %H:%M') if last_message else "",
            'unread_count': unread_count
        })
    
    return render_template("alumni/messages.html", user=user, conversations=conversation_list)

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

@views.route("/alumni/settings")
def alumni_settings():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import AlumniProfile
    profile = AlumniProfile.query.filter_by(user_id=user.id).first()
    
    return render_template("alumni/settings.html", user=user, profile=profile)

@views.route("/debug-routes")
def debug_routes():
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({        
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'url': str(rule)
        })
    return jsonify(routes)
# In views_routes.py
@views.route("/test-email")
def test_email():
    from ..services.email_service import send_email
    
    result = send_email(
        to_email="your-email@gmail.com",
        subject="Test Email from Alumni Portal",
        template='test_email',
        name="Test User",
        app_url=os.getenv('APP_URL', 'http://localhost:5000')
    )
    
    if result:
        return "✅ Test email sent! Check your inbox."
    else:
        return "❌ Failed to send test email. Check console for errors."
    
@views.route("/alumni/resources")
def alumni_resources():
    
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorResource
    
    resources = MentorResource.query.filter_by(
        alumni_id=user.id
    ).order_by(MentorResource.created_at.desc()).all()
    
    return render_template("alumni/resources.html", user=user, resources=resources)

@views.route("/alumni/chat/<int:conversation_id>")
def alumni_chat(conversation_id):
    """View a specific conversation for alumni"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Conversation, Message
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if the user is part of this conversation (as either student OR alumni)
    if conversation.student_id != user.id and conversation.alumni_id != user.id:
        flash('You do not have access to this conversation.', 'error')
        return redirect(url_for('views.alumni_messages'))
    
    # Mark messages as read
    messages = Message.query.filter_by(
        conversation_id=conversation_id,
        is_read=False
    ).all()
    
    for msg in messages:
        if msg.sender_id != user.id:
            msg.is_read = True
    db.session.commit()
    
    return render_template("alumni/chat.html", user=user, conversation_id=conversation_id)

@views.route("/alumni/start-chat/<int:other_user_id>")
def alumni_start_chat(other_user_id):
    """Start a new chat with another alumni or mentee"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    other_user = User.query.get_or_404(other_user_id)
    
    # Check if they are connected (for alumni-alumni messaging)
    from ..models.user import Connection
    
    # Check if they are connected (accepted connection)
    connection = Connection.query.filter(
        ((Connection.user_id == user.id) & (Connection.connected_user_id == other_user_id)) |
        ((Connection.user_id == other_user_id) & (Connection.connected_user_id == user.id)),
        Connection.status == 'accepted'
    ).first()
    
    # Check if it's a mentorship relationship (for student-alumni)
    from ..models.user import MentorshipRequest
    mentorship = MentorshipRequest.query.filter(
        ((MentorshipRequest.student_id == user.id) & (MentorshipRequest.alumni_id == other_user_id)) |
        ((MentorshipRequest.student_id == other_user_id) & (MentorshipRequest.alumni_id == user.id)),
        MentorshipRequest.status == 'accepted',
        MentorshipRequest.payment_status == 'paid'
    ).first()
    
 
    if not connection and not mentorship and user.id != other_user_id:
        flash('You can only message your connections or active mentees/mentors.', 'error')
        return redirect(url_for('views.alumni_connections'))
    
    
    
   
    conv = Conversation.query.filter(
        ((Conversation.student_id == user.id) & (Conversation.alumni_id == other_user_id)) |
        ((Conversation.student_id == other_user_id) & (Conversation.alumni_id == user.id))
    ).first()
    
    if not conv:
       
        conv = Conversation(
            student_id=min(user.id, other_user_id),
            alumni_id=max(user.id, other_user_id)
        )
        db.session.add(conv)
        db.session.commit()
    
    # Redirect to the chat page
    return redirect(url_for('views.alumni_chat', conversation_id=conv.id))

@views.route("/alumni/schedule-session/<int:mentee_id>", methods=['GET', 'POST'])
def schedule_session(mentee_id):
    """Schedule a mentorship session with resources"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
   
    mentorship = MentorshipRequest.query.filter_by(
        alumni_id=user.id,
        student_id=mentee_id,
        status='accepted',
        payment_status='paid'
    ).first()
    
    if not mentorship:
        flash('You can only schedule sessions with your active mentees.', 'error')
        return redirect(url_for('views.alumni_mentorship'))
    
    student = User.query.get(mentee_id)
    
    if request.method == 'POST':
        from ..models.user import MentorshipSession, SessionResource
        import os
        from werkzeug.utils import secure_filename
        
        # Create session
        session = MentorshipSession(
            mentorship_request_id=mentorship.id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            session_date=datetime.strptime(request.form.get('session_date'), '%Y-%m-%dT%H:%M'),
            duration_minutes=int(request.form.get('duration', 60)),
            meeting_link=request.form.get('meeting_link'),
            meeting_platform=request.form.get('meeting_platform'),
            location=request.form.get('location')
        )
        db.session.add(session)
        db.session.commit()
        
        # Handle resources
        resource_title = request.form.get('resource_title')
        resource_description = request.form.get('resource_description')
        resource_type = request.form.get('resource_type')
        external_link = request.form.get('external_link')
        
        # Handle file upload
        file = request.files.get('resource_file')
        file_path = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'uploads', 'session_resources')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = f'/static/uploads/session_resources/{filename}'
            file.save(os.path.join(upload_dir, filename))
        
        if resource_title:
            resource = SessionResource(
                session_id=session.id,
                title=resource_title,
                description=resource_description,
                resource_type=resource_type,
                file_path=file_path,
                external_link=external_link
            )
            db.session.add(resource)
            db.session.commit()
        
       
        from ..services.notification_service import NotificationService
        NotificationService.create_notification(
            user_id=mentee_id,
            sender_id=user.id,
            title=f"New Session Scheduled: {session.title}",
            message=f"{user.full_name} has scheduled a mentorship session with you.",
            notification_type='session_scheduled',
            reference_id=session.id,
            reference_type='session'
        )
        
        flash('Session scheduled successfully!', 'success')
        return redirect(url_for('views.mentorship', session_id=session.id))
    
    return render_template("alumni/schedule_session.html", user=user, student=student, mentorship=mentorship)

@views.route("/session/<int:session_id>")
def view_session(session_id):
    """View session details - works for both alumni and students"""
    user = get_current_user()
    
    if not user:
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipSession, SessionResource, MentorshipRequest
    
    
    session_data  = MentorshipSession.query.get_or_404(session_id)
    mentorship = MentorshipRequest.query.get(session_data.mentorship_request_id)  
    resources = SessionResource.query.filter_by(session_id=session_id).all()
    
    if user.role == 'alumni':
        if mentorship.alumni_id != user.id:
            flash('You do not have access to this session.', 'error')
            return redirect(url_for('views.alumni_dashboard'))
        
        return render_template("alumni/view_session.html", 
                             user=user, 
                             session_data=session_data,  
                             resources=resources,
                             mentorship=mentorship)
    
    elif user.role == 'student':
        if mentorship.student_id != user.id:
            flash('You do not have access to this session.', 'error')
            return redirect(url_for('student.dashboard'))
        
        return render_template("student/view_session.html", 
                             user=user, 
                             session_data=MentorshipSession,
                             resources=resources,
                             mentorship=mentorship)
    
    else:
        flash('Access denied.', 'error')
        return redirect(url_for('views.login_page'))
    
@views.route("/alumni/edit-session/<int:session_id>", methods=['GET', 'POST'])
def edit_session(session_id):
    """Edit an existing mentorship session"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipSession, SessionResource, MentorshipRequest
    from datetime import datetime
    
    session_data = MentorshipSession.query.get_or_404(session_id)  
    mentorship = MentorshipRequest.query.get(session_data.mentorship_request_id)
    
    
    if mentorship.alumni_id != user.id:
        flash('You do not have permission to edit this session.', 'error')
        return redirect(url_for('views.alumni_mentorship'))
    
    resources = SessionResource.query.filter_by(session_id=session_id).all()
    
    if request.method == 'POST':
        try:
          
            session_data.title = request.form.get('title')
            session_data.description = request.form.get('description')
            session_data.session_date = datetime.strptime(request.form.get('session_date'), '%Y-%m-%dT%H:%M')
            session_data.duration_minutes = int(request.form.get('duration', 60))
            session_data.meeting_link = request.form.get('meeting_link')
            session_data.meeting_platform = request.form.get('meeting_platform')
            session_data.location = request.form.get('location')
            session_data.status = request.form.get('status', 'scheduled')
            
            db.session.commit()
            
           
            
            flash('Session updated successfully!', 'success')
            return redirect(url_for('views.view_session', session_id=session_data.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating session: {str(e)}', 'error')
            return redirect(url_for('views.edit_session', session_id=session_data.id))
    
    return render_template("alumni/edit_session.html", 
                         user=user, 
                         session_data=session_data,  # Changed to session_data
                         resources=resources,
                         mentorship=mentorship)

@views.route("/alumni/delete-session/<int:session_id>", methods=['POST'])
def delete_session(session_id):
    """Delete a mentorship session"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipSession, SessionResource, MentorshipRequest
    
    session = MentorshipSession.query.get_or_404(session_id)
    mentorship = MentorshipRequest.query.get(session.mentorship_request_id)
    
    # Check if this alumni owns this session
    if mentorship.alumni_id != user.id:
        flash('You do not have permission to delete this session.', 'error')
        return redirect(url_for('views.alumni_mentorship'))
    
    try:
        # Delete all resources first
        SessionResource.query.filter_by(session_id=session_id).delete()
        # Delete the session
        db.session.delete(session)
        db.session.commit()
        
        # Send notification to mentee about deleted session
        from ..services.notification_service import NotificationService
        NotificationService.create_notification(
            user_id=mentorship.student_id,
            sender_id=user.id,
            title=f"Session Cancelled: {session.title}",
            message=f"The session scheduled for {session.session_date.strftime('%b %d, %Y at %I:%M %p')} has been cancelled.",
            notification_type='session_cancelled',
            reference_id=session.id,
            reference_type='session'
        )
        
        flash('Session deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting session: {str(e)}', 'error')
    
    return redirect(url_for('views.alumni_mentorship'))

@views.route("/alumni/connections")
def alumni_connections():
    """Show all connections for alumni"""
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Connection, User, AlumniProfile
    
    # Get all accepted connections
    connections = Connection.query.filter(
        ((Connection.user_id == user.id) | (Connection.connected_user_id == user.id)),
        Connection.status == 'accepted'
    ).all()
    
    connection_list = []
    for conn in connections:
        other_id = conn.connected_user_id if conn.user_id == user.id else conn.user_id
        other_user = User.query.get(other_id)
        if other_user:
         
            alumni_profile = AlumniProfile.query.filter_by(user_id=other_user.id).first() if other_user.role == 'alumni' else None
            
            connection_list.append({
                'id': other_user.id,
                'name': other_user.full_name,
                'role': other_user.role,
                'avatar': other_user.full_name[:2].upper(),
                'job_title': alumni_profile.job_title if alumni_profile else None,
                'company': alumni_profile.company if alumni_profile else None
            })
    
    return render_template("alumni/connections.html", user=user, connections=connection_list)





