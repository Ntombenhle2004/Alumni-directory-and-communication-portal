from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from ..config.db import db
from ..models.user import User, AlumniProfile, StudentProfile, Rating, MentorshipRequest
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
    user = get_current_user()
    if not user or user.role != 'student':
        flash('Please login as a student to access the dashboard.', 'error')
        return redirect(url_for('views.login_page'))
    
    
    student_profile = StudentProfile.query.filter_by(user_id=user.id).first()
    
    
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
        flash('Please login to view alumni profiles.', 'error')
        return redirect(url_for('views.login_page'))
    
    alumni = User.query.get_or_404(alumni_id)
    if alumni.role != 'alumni':
        flash('User is not an alumni.', 'error')
        return redirect(url_for('student.dashboard'))
    
    profile = AlumniProfile.query.filter_by(user_id=alumni_id).first()
    
   
    ratings = Rating.query.filter_by(alumni_id=alumni_id).all()
    avg_rating = sum(r.score for r in ratings) / len(ratings) if ratings else 0
    
    
    user_rating = Rating.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id
    ).first()
    
    mentorship_request = MentorshipRequest.query.filter_by(
        student_id=user.id,
        alumni_id=alumni_id
    ).first()
    
    return render_template("student/view_alumni.html",
                         user=user,
                         alumni=alumni,
                         profile=profile,
                         ratings=ratings,
                         avg_rating=avg_rating,
                         user_rating=user_rating,
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

@student_bp.route("/my-mentors")
def my_mentors():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    mentorships = MentorshipRequest.query.filter_by(
        student_id=user.id,
        status='accepted'
    ).all()
    
    return render_template("student/my_mentors.html",
                         user=user,
                         mentorships=mentorships)

@student_bp.route("/mentorship-requests")
def mentorship_requests():
    user = get_current_user()
    if not user or user.role != 'student':
        return redirect(url_for('views.login_page'))
    
    
    pending_requests = MentorshipRequest.query.filter_by(
        student_id=user.id,
        status='pending'
    ).all()
    
   
    rejected_requests = MentorshipRequest.query.filter_by(
        student_id=user.id,
        status='rejected'
    ).all()
    
    return render_template("student/mentorship_requests.html",
                         user=user,
                         pending_requests=pending_requests,
                         rejected_requests=rejected_requests)


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