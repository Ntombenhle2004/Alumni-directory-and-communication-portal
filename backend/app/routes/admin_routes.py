from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from ..models.user import User, MentorshipRequest, Event, Post, Report
from ..config.db import db
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/test')
def test():
    return "Admin blueprint is working!"

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('views.login_page'))
        
        user = User.query.get(session['user_id'])
        
        if not user or user.role != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('views.home'))
        
        return f(*args, **kwargs)
    return decorated_function

# Helper to get current user
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# Helper to calculate monthly revenue
def calculate_monthly_revenue():
    """Calculate total revenue from the current month"""
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    # Get paid mentorships this month
    paid_mentorships = MentorshipRequest.query.filter(
        MentorshipRequest.payment_status == 'paid',
        MentorshipRequest.payment_date >= start_of_month
    ).all()
    
    revenue = sum([m.payment_amount for m in paid_mentorships if m.payment_amount])
    return revenue

# Dashboard
@admin_bp.route('/')
@admin_required
def dashboard():
    user = get_current_user()
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    # Calculate monthly revenue
    paid_mentorships = MentorshipRequest.query.filter(
        MentorshipRequest.payment_status == 'paid',
        MentorshipRequest.payment_date >= start_of_month
    ).all()
    revenue_this_month = sum([m.payment_amount for m in paid_mentorships if m.payment_amount])
    
    # Simple stats
    stats = {
        'total_users': User.query.count(),
        'total_alumni': User.query.filter_by(role='alumni').count(),
        'total_students': User.query.filter_by(role='student').count(),
        'active_mentorships': MentorshipRequest.query.filter_by(status='accepted').count(),
        'pending_mentorships': MentorshipRequest.query.filter_by(status='pending').count(),
        'total_events': Event.query.count(),
        'upcoming_events': Event.query.filter(Event.start_date > now).count(),
        'total_posts': Post.query.count(),
        'pending_reports': Report.query.filter_by(status='pending').count(),
        'revenue_this_month': revenue_this_month
    }
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Chart data (last 6 months)
    months = []
    user_growth = []
    revenue_data = []
    
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1)
        
        # Calculate next month start
        if month_date.month == 12:
            month_end = datetime(month_date.year + 1, 1, 1)
        else:
            month_end = datetime(month_date.year, month_date.month + 1, 1)
        
        months.append(month_start.strftime('%b'))
        
        # New users this month
        new_users = User.query.filter(
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()
        user_growth.append(new_users)
        
        # Revenue this month
        month_revenue = sum([m.payment_amount for m in MentorshipRequest.query.filter(
            MentorshipRequest.payment_status == 'paid',
            MentorshipRequest.payment_date >= month_start,
            MentorshipRequest.payment_date < month_end
        ).all() if m.payment_amount])
        revenue_data.append(month_revenue)
    
    return render_template('admin/dashboard.html', 
                         user=user, 
                         stats=stats,
                         recent_users=recent_users,
                         months=months,
                         user_growth=user_growth,
                         revenue_data=revenue_data)

# User Management
@admin_bp.route('/users')
@admin_required
def users():
    user = get_current_user()
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', user=user, users=users)

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@admin_required
def change_role(user_id):
    target_user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')
    
    if new_role in ['student', 'alumni', 'admin']:
        target_user.role = new_role
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid role'}), 400

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Deactivate/reactivate a user"""
    target_user = User.query.get_or_404(user_id)
    
    # Add is_active field if it doesn't exist, otherwise toggle
    if not hasattr(target_user, 'is_active'):
        from sqlalchemy import Column, Boolean
        # You'd need to add this field to your model
        target_user.is_active = not getattr(target_user, 'is_active', True)
    
    # For now, just return success
    return jsonify({'success': True, 'is_active': getattr(target_user, 'is_active', True)})

# Mentorship Management
@admin_bp.route('/mentorships')
@admin_required
def mentorships():
    user = get_current_user()
    requests = MentorshipRequest.query.order_by(MentorshipRequest.request_date.desc()).all()
    return render_template('admin/mentorships.html', user=user, requests=requests)

@admin_bp.route('/mentorships/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_mentorship(request_id):
    req = MentorshipRequest.query.get_or_404(request_id)
    req.status = 'accepted'
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/mentorships/<int:request_id>/delete', methods=['POST'])
@admin_required
def delete_mentorship(request_id):
    req = MentorshipRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    return jsonify({'success': True})

# Event Management
@admin_bp.route('/events')
@admin_required
def events():
    user = get_current_user()
    events = Event.query.order_by(Event.created_at.desc()).all()
    now = datetime.utcnow()
    return render_template('admin/events.html', user=user, events=events, now=now)

@admin_bp.route('/events/<int:event_id>/approve', methods=['POST'])
@admin_required
def approve_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.is_published = True
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'success': True})

# Post Moderation
@admin_bp.route('/posts')
@admin_required
def posts():
    user = get_current_user()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', user=user, posts=posts)

@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True})

# Reports
@admin_bp.route('/reports')
@admin_required
def reports():
    user = get_current_user()
    reports = Report.query.order_by(Report.created_at.desc()).all()
    pending_count = Report.query.filter_by(status='pending').count()
    resolved_this_month = Report.query.filter(
        Report.status == 'resolved',
        Report.resolved_at >= datetime.utcnow().replace(day=1)
    ).count()
    
    return render_template('admin/reports.html', 
                         user=user, 
                         reports=reports,
                         pending_count=pending_count,
                         resolved_this_month=resolved_this_month,
                         avg_response_time=24)

@admin_bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = 'resolved'
    report.resolved_at = datetime.utcnow()
    report.resolved_by = session['user_id']
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@admin_required
def dismiss_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = 'dismissed'
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/reports/<int:report_id>/delete', methods=['POST'])
@admin_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    return jsonify({'success': True})

# Settings
@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    user = get_current_user()
    
    if request.method == 'POST':
        # Simple settings update
        settings = {
            'mentorship_price_monthly': request.form.get('mentorship_price_monthly', '250'),
            'mentorship_price_semester': request.form.get('mentorship_price_semester', '1250'),
            'student_subscription_price': request.form.get('student_subscription_price', '5000'),
            'default_event_capacity': request.form.get('default_event_capacity', '100'),
            'site_name': request.form.get('site_name', 'Alumni Portal')
        }
        
        # Save to system_settings table
        try:
            from ..models.user import SystemSetting
            for key, value in settings.items():
                setting = SystemSetting.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = SystemSetting(key=key, value=value)
                    db.session.add(setting)
            db.session.commit()
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving settings: {str(e)}', 'error')
        
        return redirect(url_for('admin.settings'))
    
    # Load existing settings
    settings = {}
    try:
        from ..models.user import SystemSetting
        db_settings = SystemSetting.query.all()
        for s in db_settings:
            settings[s.key] = s.value
    except:
        pass
    
    
    return render_template('admin/settings.html', user=user, settings=settings)

@admin_bp.route('/transactions')
@admin_required
def transactions():
    user = get_current_user()
    from ..models.user import MentorshipRequest, EventRegistration
    
    # Get all transactions
    mentorship_payments = MentorshipRequest.query.filter_by(payment_status='paid').all()
    event_payments = EventRegistration.query.filter_by(payment_status='paid').all()
    
    transactions = []
    for m in mentorship_payments:
        transactions.append({
            'id': m.id,
            'type': 'mentorship',
            'user': User.query.get(m.student_id),
            'amount': m.payment_amount,
            'date': m.payment_date,
            'status': 'paid'
        })
    
    for e in event_payments:
        transactions.append({
            'id': e.id,
            'type': 'event',
            'user': User.query.get(e.user_id),
            'amount': e.payment_amount,
            'date': e.payment_date,
            'status': 'paid'
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
    
    return render_template('admin/transactions.html', user=user, transactions=transactions)

@admin_bp.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    """Add a new user"""
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    role = data.get('role', 'student')
    password = data.get('password')
    
    if not full_name or not email:
        return jsonify({'error': 'Name and email required'}), 400
    
    # Check if user exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({'error': 'Email already exists'}), 400
    
    # Hash password
    from ..services.auth_service import hash_password
    hashed_password = hash_password(password) if password else hash_password('password123')
    
    # Create user
    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=hashed_password,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'success': True, 'user_id': new_user.id})

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """Reset a user's password"""
    target_user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'error': 'Password required'}), 400
    
    from ..services.auth_service import hash_password
    target_user.password_hash = hash_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True})

@admin_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    target_user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if target_user.id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(target_user)
    db.session.commit()
    
    return jsonify({'success': True})