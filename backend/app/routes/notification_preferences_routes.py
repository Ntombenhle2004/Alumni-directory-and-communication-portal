from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from ..models.user import NotificationPreference, User
from ..config.db import db
from ..services.notification_service import NotificationService

preferences_bp = Blueprint('preferences', __name__, url_prefix='/preferences')

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@preferences_bp.route('/notifications')
def notification_preferences():
    """Render notification preferences page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    # Get or create preferences
    prefs = NotificationPreference.query.filter_by(user_id=user.id).first()
    if not prefs:
        prefs = NotificationService.create_default_preferences(user.id)
    
    return render_template('notifications/preferences.html', 
                         user=user,
                         prefs=prefs)

@preferences_bp.route('/notifications/update', methods=['POST'])
def update_preferences():
    """Update notification preferences"""
    user = get_current_user()
    if not user:
        flash('Please login to update preferences.', 'error')
        return redirect(url_for('views.login_page'))
    
    prefs = NotificationPreference.query.filter_by(user_id=user.id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=user.id)
        db.session.add(prefs)
    
    # Update email preferences
    prefs.email_messages = request.form.get('email_messages') == 'on'
    prefs.email_mentorship_requests = request.form.get('email_mentorship_requests') == 'on'
    prefs.email_mentorship_responses = request.form.get('email_mentorship_responses') == 'on'
    prefs.email_event_reminders = request.form.get('email_event_reminders') == 'on'
    prefs.email_event_updates = request.form.get('email_event_updates') == 'on'
    prefs.email_weekly_digest = request.form.get('email_weekly_digest') == 'on'
    
    # Update in-app preferences
    prefs.inapp_messages = request.form.get('inapp_messages') == 'on'
    prefs.inapp_mentorship_requests = request.form.get('inapp_mentorship_requests') == 'on'
    prefs.inapp_mentorship_responses = request.form.get('inapp_mentorship_responses') == 'on'
    prefs.inapp_event_reminders = request.form.get('inapp_event_reminders') == 'on'
    prefs.inapp_event_updates = request.form.get('inapp_event_updates') == 'on'
    
    # Update reminder settings
    prefs.reminder_days_before = int(request.form.get('reminder_days_before', 1))
    prefs.reminder_time = request.form.get('reminder_time', '09:00')
    
    # Update quiet hours
    prefs.quiet_hours_enabled = request.form.get('quiet_hours_enabled') == 'on'
    prefs.quiet_hours_start = request.form.get('quiet_hours_start')
    prefs.quiet_hours_end = request.form.get('quiet_hours_end')
    
    db.session.commit()
    flash('Notification preferences updated successfully!', 'success')
    
    return redirect(url_for('preferences.notification_preferences'))