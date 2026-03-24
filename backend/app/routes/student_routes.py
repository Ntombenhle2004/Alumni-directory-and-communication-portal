from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from ..config.db import db
from ..models.user import MentorshipSession, SessionResource, User, AlumniProfile, StudentProfile, Rating, MentorshipRequest
from sqlalchemy import or_
import math
from datetime import datetime

student_bp = Blueprint("student", __name__, url_prefix="/student")


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@student_bp.route("/dashboard")
def dashboard():

    print("="*50)
    print("STUDENT DASHBOARD ROUTE ACCESSED")
    
    user = get_current_user()
    print(f"User: {user}")
    if not user or user.role != 'student':
        flash('Please login as a student to access the dashboard.', 'error')
        return redirect(url_for('views.login_page'))
    
    
    student_profile = StudentProfile.query.filter_by(user_id=user.id).first()
    print(f"Student profile: {student_profile}")
    
    
    page = request.args.get('page', 1, type=int)
    per_page = 12
    search_query = request.args.get('q', '')
    industry_filter = request.args.get('industry', '')
    mentorship_filter = request.args.get('mentorship', '')
    sort_by = request.args.get('sort', 'recent')
    
   
    query = User.query.filter_by(role='alumni')
    
   
    query = query.join(AlumniProfile, User.id == AlumniProfile.user_id)
    
    if search_query:
        query = query.filter(
            or_(
                User.full_name.ilike(f'%{search_query}%'),
                AlumniProfile.job_title.ilike(f'%{search_query}%'),
                AlumniProfile.company.ilike(f'%{search_query}%'),
                AlumniProfile.industry.ilike(f'%{search_query}%'),
                AlumniProfile.skills.ilike(f'%{search_query}%')
            )
        )
    
   
    if industry_filter:
        query = query.filter(AlumniProfile.industry == industry_filter)
    
    
    if mentorship_filter == 'available':
        query = query.filter(AlumniProfile.mentorship_available == True)
    
    
    if sort_by == 'name':
        query = query.order_by(User.full_name)
    elif sort_by == 'rating':
        query = query.order_by(AlumniProfile.rating_count.desc())
    else: 
        query = query.order_by(User.created_at.desc())
    
    
    total_alumni = query.count()
    total_pages = math.ceil(total_alumni / per_page)
    
   
    alumni = query.offset((page - 1) * per_page).limit(per_page).all()
    
  
    alumni_list = []
    for a in alumni:
        profile = AlumniProfile.query.filter_by(user_id=a.id).first()
        
        if profile and profile.rating_count and profile.rating_count > 0:
            ratings = Rating.query.filter_by(alumni_id=a.id).all()
            avg_rating = sum(r.score for r in ratings) / len(ratings) if ratings else 0
            profile.rating_avg = avg_rating
        
        alumni_list.append({
            'id': a.id,
            'full_name': a.full_name,
            'email': a.email,
            'profile': profile
        })
    
    return render_template("student/dashboard.html",
                         user=user,
                         student_profile=student_profile,
                         alumni_list=alumni_list,
                         total_alumni=total_alumni,
                         current_page=page,
                         total_pages=total_pages,
                         search_query=search_query,
                         industry_filter=industry_filter,
                         mentorship_filter=mentorship_filter,
                         sort_by=sort_by)

@student_bp.route("/search")
def search_alumni():
   
    return redirect(url_for('student.dashboard', **request.args))

@student_bp.route("/alumni/<int:alumni_id>")
def view_alumni(alumni_id):
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    alumni = User.query.get_or_404(alumni_id)
    if alumni.role != 'alumni':
        flash('User is not an alumni.', 'error')
        return redirect(url_for('student.dashboard'))
    
    profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()
    
    # Check connection status
    from ..models.user import ConnectionRequest
    connection = ConnectionRequest.query.filter(
        ((ConnectionRequest.sender_id == user.id) & (ConnectionRequest.receiver_id == alumni_id)) |
        ((ConnectionRequest.sender_id == alumni_id) & (ConnectionRequest.receiver_id == user.id))
    ).first()
    
    connection_status = 'none'
    if connection:
        connection_status = connection.status
    
    # Check mentorship request
    mentorship_request = MentorshipRequest.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id
    ).first()
    
    print("="*50)
    print(f"VIEW ALUMNI DEBUG:")
    print(f"Alumni ID: {alumni_id}")
    print(f"Student ID: {user.id}")
    print(f"Connection Status: {connection_status}")
    print(f"Profile exists: {profile is not None}")
    if profile:
        print(f"Mentorship Available: {profile.mentorship_available}")
    print(f"Mentorship Request: {mentorship_request}")
    print("="*50)
    if mentorship_request:
        print(f"Mentorship Request Status: {mentorship_request.status}")
    
    return render_template("student/view_alumni.html",
                         user=user,
                         alumni=alumni,
                         profile=profile,
                         connection_status=connection_status,
                         mentorship_request=mentorship_request)

@student_bp.route("/alumni/<int:alumni_id>/rate", methods=['POST'])
def rate_alumni(alumni_id):
    user = get_current_user()
    if not user or user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    score = data.get('score')
    comment = data.get('comment', '')
    
    if not score or int(score) < 1 or int(score) > 5:
        return jsonify({'error': 'Invalid rating score'}), 400
    
    existing = Rating.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id
    ).first()
    
    if existing:
        existing.score = int(score)
        existing.comment = comment
    else:
        rating = Rating(
            student_id=user.id,
            alumni_id=alumni_id,
            score=int(score),
            comment=comment
        )
        db.session.add(rating)
        
        alumni_profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()
        if alumni_profile:
            alumni_profile.rating_count = (alumni_profile.rating_count or 0) + 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Rating submitted successfully'})

@student_bp.route("/request-mentorship/<int:alumni_id>", methods=['POST'])
def request_mentorship(alumni_id):
    user = get_current_user()
    if not user or user.role != 'student':
        flash('Please login to request mentorship.', 'error')
        return redirect(url_for('views.login_page'))
    
    existing = MentorshipRequest.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id
    ).first()
    
    if existing:
        flash('You have already sent a mentorship request to this alumni.', 'info')
    else:
        message = request.form.get('message', '')
        mentorship_request = MentorshipRequest(
            student_id=user.id,
            alumni_id=alumni_id,
            message=message,
            status='pending'
        )
        db.session.add(mentorship_request)
        db.session.commit()
        flash('Mentorship request sent successfully!', 'success')
    
    return redirect(url_for('student.view_alumni', alumni_id=alumni_id))


@student_bp.route("/mentorship-requests")
def mentorship_requests():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipRequest, User
    
    # Get all requests sent by this student
    all_requests = MentorshipRequest.query.filter_by(
        student_id=user.id
    ).order_by(MentorshipRequest.request_date.desc()).all()
    
    # Categorize requests by status
    pending_requests = []
    accepted_requests = []
    rejected_requests = []
    
    for request in all_requests:
        # Get alumni name
        alumni = User.query.get(request.alumni_id)
        request.alumni_name = alumni.full_name if alumni else "Unknown Alumni"
        
        if request.status.lower() == 'pending':
            pending_requests.append(request)
        elif request.status.lower() == 'accepted':
            accepted_requests.append(request)
        elif request.status.lower() == 'rejected':
            rejected_requests.append(request)
    
    return render_template("student/mentorship_requests.html",
                         user=user,
                         pending_requests=pending_requests,
                         accepted_requests=accepted_requests,
                         rejected_requests=rejected_requests)

@student_bp.route("/cancel-request/<int:request_id>", methods=['POST'])
def cancel_mentorship_request(request_id):
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipRequest
    
    request = MentorshipRequest.query.get_or_404(request_id)
    
    # Ensure this request belongs to the current user
    if request.student_id != user.id:
        flash('You do not have permission to cancel this request.', 'error')
        return redirect(url_for('student.mentorship_requests'))
    
    # Only allow cancellation of pending requests
    if request.status.lower() == 'pending':
        db.session.delete(request)
        db.session.commit()
        flash('Mentorship request cancelled successfully.', 'success')
    else:
        flash('Cannot cancel a request that has already been processed.', 'error')
    
    return redirect(url_for('student.mentorship_requests'))


@student_bp.route("/profile")
def my_profile():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('profile.student_profile_view'))
    
    profile_data = StudentProfile.query.filter_by(user_id=user.id).first()
    
    return render_template("student/profile.html", 
                         user=user, 
                        profile_data=profile_data)

@student_bp.route("/profile/edit", methods=['GET', 'POST'])
def edit_profile():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    student_profile = StudentProfile.query.filter_by(user_id=user.id).first()
    
    if request.method == 'POST':
        
        student_profile.course = request.form.get('course')
        student_profile.graduation_year = request.form.get('graduation_year')
        student_profile.interests = request.form.get('interests')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.my_profile'))
    
    return render_template("student/edit_profile.html", 
                         user=user, 
                         profile=student_profile)

@student_bp.route("/messages")
def messages():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Conversation, Message
    
    conversations = Conversation.query.filter_by(student_id=user.id).all()
    
    unread_count = Message.query.join(Conversation).filter(
        Conversation.student_id == user.id,
        Message.is_read == False,
        Message.sender_id != user.id
    ).count()
    
    return render_template("student/messages.html",
                         user=user,
                         conversations=conversations,
                         unread_count=unread_count)

@student_bp.route("/browse-alumni")
def browse_alumni():
    
    return redirect(url_for('student.dashboard'))

@student_bp.route("/events")
def events():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Event, EventRegistration
    from datetime import datetime
    
   
    upcoming_events = Event.query.filter(
        Event.start_date > datetime.utcnow(),
        Event.is_published == True
    ).order_by(Event.start_date).all()
    
    my_registrations = EventRegistration.query.filter_by(
        user_id=user.id,
        status='registered'
    ).all()
    my_events = [r.event for r in my_registrations]
    
    return render_template("student/events.html",
                         user=user,
                         upcoming_events=upcoming_events,
                         my_events=my_events)

@student_bp.route("/subscription")
def subscription():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Subscription
    
    subscription = Subscription.query.filter_by(student_id=user.id).first()
    
    return render_template("student/subscription.html",
                         user=user,
                         subscription=subscription)

@student_bp.route("/settings")
def settings():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    return render_template("student/settings.html", user=user)

@student_bp.route("/notifications")
def student_notifications():
    """Render student notifications page"""
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Notification
    
    # Get all notifications for this student
    notifications = Notification.query.filter_by(
        user_id=user.id,
        is_archived=False
    ).order_by(Notification.created_at.desc()).all()
    
    # Add sender info
    for n in notifications:
        if n.sender_id:
            n.sender = User.query.get(n.sender_id)
    
    return render_template("student/notifications.html",
                         user=user,
                         notifications=notifications)

@student_bp.route("/my-mentors")
def my_mentors():
    """Show all accepted mentors for the student"""
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipRequest, User, AlumniProfile
    
    # Get all accepted mentorship requests
    # For now, don't filter by payment_status to debug
    mentorship_requests = MentorshipRequest.query.filter_by(
        student_id=user.id,
        status='accepted'
    ).order_by(MentorshipRequest.request_date.desc()).all()

    pending_requests = MentorshipRequest.query.filter_by(
        student_id=user.id,
        status='pending'
    ).order_by(MentorshipRequest.request_date.desc()).all()
    
    print(f"Found {len(mentorship_requests)} accepted mentorship requests")

    from datetime import datetime
    upcoming_sessions = []
    for req in mentorship_requests:
        sessions = MentorshipSession.query.filter_by(
            mentorship_request_id=req.id,
            status='scheduled'
        ).filter(MentorshipSession.session_date >= datetime.utcnow()).order_by(MentorshipSession.session_date.asc()).all()
        
        for session in sessions:
            alumni = User.query.get(req.alumni_id)
            upcoming_sessions.append({
                'id': session.id,
                'title': session.title,
                'mentor_name': alumni.full_name if alumni else 'Mentor',
                'session_date': session.session_date,
                'duration_minutes': session.duration_minutes,
                'meeting_link': session.meeting_link,
                'location': session.location
            })
    
    mentors = []
    for req in mentorship_requests:
        print(f"Request {req.id}: status={req.status}, payment={req.payment_status}")
        alumni = User.query.get(req.alumni_id)
        if alumni:
            profile = AlumniProfile.query.filter_by(user_id=alumni.id).first()
            alumni.profile = profile
            alumni.connected_since = req.response_date.strftime('%b %Y') if req.response_date else 'Recently'
            mentors.append(alumni)
    
    return render_template("student/my_mentors.html", user=user, mentors=mentors, upcoming_sessions_list=upcoming_sessions[:5], pending_requests=pending_requests)

# In student_routes.py, add this temporary debug route
@student_bp.route("/debug-mentors")
def debug_mentors():
    user = get_current_user()
    if not user:
        return "Not logged in"
    
    from ..models.user import MentorshipRequest
    
    requests = MentorshipRequest.query.filter_by(student_id=user.id).all()
    
    result = []
    for req in requests:
        result.append({
            'id': req.id,
            'alumni_id': req.alumni_id,
            'status': req.status,
            'payment_status': req.payment_status,
            'request_date': str(req.request_date),
            'response_date': str(req.response_date)
        })
    
    return result

@student_bp.route("/start-chat/<int:alumni_id>")
def start_chat(alumni_id):
    """Start a new chat with a mentor"""
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    # Check if the user is connected (has an accepted and paid mentorship)
    from ..models.user import MentorshipRequest
    
    mentorship = MentorshipRequest.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id,
        status='accepted',
        payment_status='paid'
    ).first()
    
    if not mentorship:
        flash('You can only message your active mentors.', 'error')
        return redirect(url_for('student.my_mentors'))
    
    # Use the existing chat service to start conversation
    from ..services.chat_service import start_conversation_logic
    
    conv, error = start_conversation_logic({
        'student_id': user.id,
        'alumni_id': alumni_id
    })
    
    if error:
        flash('Error starting conversation: ' + error, 'error')
        return redirect(url_for('student.my_mentors'))
    
    # Redirect to the chat page
    return redirect(url_for('student.chat', conversation_id=conv.id))

@student_bp.route("/chat/<int:conversation_id>")
def chat(conversation_id):
    """View a specific conversation"""
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import Conversation, Message
    
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # Check if the user is part of this conversation
    if conversation.student_id != user.id and conversation.alumni_id != user.id:
        flash('You do not have access to this conversation.', 'error')
        return redirect(url_for('student.dashboard'))
    
    # Mark messages as read
    messages = Message.query.filter_by(
        conversation_id=conversation_id,
        is_read=False
    ).all()
    
    for msg in messages:
        if msg.sender_id != user.id:
            msg.is_read = True
    db.session.commit()
    
    return render_template("student/chat.html", user=user, conversation_id=conversation_id)

@student_bp.route("/mentor-resources/<int:alumni_id>")
def mentor_resources(alumni_id):
    """View resources shared by a mentor"""
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    # Check if this is an active mentor
    from ..models.user import MentorshipRequest, MentorResource, User, AlumniProfile
    
    mentorship = MentorshipRequest.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id,
        status='accepted',
        payment_status='paid'
    ).first()
    
    if not mentorship:
        flash('You can only view resources from your active mentors.', 'error')
        return redirect(url_for('student.my_mentors'))
    
    # Get mentor details
    mentor = User.query.get(alumni_id)
    profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()

    sessions = MentorshipSession.query.filter_by(
        mentorship_request_id=mentorship.id
    ).order_by(MentorshipSession.session_date.desc()).all()
    
    
    # Get resources from this mentor
    resources = MentorResource.query.filter_by(
        alumni_id=alumni_id,
        is_public=True
    ).order_by(MentorResource.created_at.desc()).all()

    
    all_session_resources = []
    sessions_with_resources = []
    
    for session in sessions:
        resources = SessionResource.query.filter_by(session_id=session.id).all()
        if resources:
            session.resources = resources
            sessions_with_resources.append(session)
            all_session_resources.extend(resources)

    general_resources = []
    
    return render_template("student/mentor_resources.html", 
                         user=user, 
                         mentor=mentor, 
                         profile=profile,
                         resources=resources,
                         sessions_with_resources=sessions_with_resources,
                         general_resources=general_resources,
                         resources_count=len(all_session_resources),
                         sessions_count=len(sessions_with_resources))

@student_bp.route("/view-session/<int:session_id>")
def view_session(session_id):
    """View session details for students"""
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    from ..models.user import MentorshipSession, SessionResource, MentorshipRequest
    
    session = MentorshipSession.query.get_or_404(session_id)
    mentorship = MentorshipRequest.query.get(session.mentorship_request_id)
    
    # Check if this session belongs to the student
    if mentorship.student_id != user.id:
        flash('You do not have access to this session.', 'error')
        return redirect(url_for('student.my_mentors'))
    
    resources = SessionResource.query.filter_by(session_id=session_id).all()
    
    return render_template("student/view_session.html", 
                         user=user, 
                         session=session, 
                         resources=resources,
                         mentorship=mentorship)