from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from ..models.user import Notification, User
from ..config.db import db
from ..services.notification_service import NotificationService
from datetime import datetime

notification_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@notification_bp.route('/')
def notifications_page():
    """Render notifications page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    # Get all notifications for user
    notifications = Notification.query.filter_by(
        user_id=user.id,
        is_archived=False
    ).order_by(Notification.created_at.desc()).all()

    print(f"Found {len(notifications)} notifications for user {user.id}")
    
    unread_count = NotificationService.get_unread_count(user.id)
    
    # Choose template based on user role
    template = 'alumni/notifications.html' if user.role == 'alumni' else 'student/notifications.html'
    
    return render_template('notifications/index.html', 
                         user=user,
                         notifications=notifications,
                         unread_count=unread_count)

@notification_bp.route('/api/unread-count')
def get_unread_count():
    """API endpoint to get unread count"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    
    count = NotificationService.get_unread_count(user.id)
    return jsonify({'unread_count': count})

@notification_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
def mark_as_read(notification_id):
    """Mark a single notification as read"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.mark_as_read()
    return jsonify({'success': True})

@notification_bp.route('/mark-all-read', methods=['POST'])
def mark_all_read():
    """Mark all notifications as read"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    
    notifications = Notification.query.filter_by(user_id=user.id, is_read=False).all()
    for n in notifications:
        n.mark_as_read()
    
    return jsonify({'success': True})

@notification_bp.route('/archive/<int:notification_id>', methods=['POST'])
def archive_notification(notification_id):
    """Archive a notification"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_archived = True
    db.session.commit()
    return jsonify({'success': True})