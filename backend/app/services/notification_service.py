from ..models.user import Notification, NotificationPreference, User, MentorshipRequest, Message
from ..config.db import db
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class NotificationService:
    
    @staticmethod
    def create_notification(user_id, title, message, notification_type, sender_id=None, reference_id=None, reference_type=None):
        """Create an in-app notification"""
        try:
            # Check if user has preferences and wants this type of notification
            prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
            if prefs:
                pref_map = {
                    'message': 'inapp_messages',
                    'mentorship_request': 'inapp_mentorship_requests',
                    'mentorship_response': 'inapp_mentorship_responses',
                    'event_reminder': 'inapp_event_reminders',
                    'event_update': 'inapp_event_updates'
                }
                if notification_type in pref_map and not getattr(prefs, pref_map[notification_type]):
                    return None, "User has disabled this notification type"
            
            notification = Notification(
                user_id=user_id,
                sender_id=sender_id,
                title=title,
                message=message,
                notification_type=notification_type,
                reference_id=reference_id,
                reference_type=reference_type
            )
            db.session.add(notification)
            db.session.commit()
            return notification, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def send_email(to_email, subject, html_content, text_content=None):
        """Send an email notification"""
        try:
            # Get email settings from environment variables
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            from_email = os.getenv('FROM_EMAIL', 'noreply@alumniportal.com')
            
            if not smtp_username or not smtp_password:
                print("Email credentials not configured. Skipping email send.")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            # Add plain text version
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            # Add HTML version
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def notify_mentorship_request(request_id):
        """Send notification when a student requests mentorship"""
        try:
            request = MentorshipRequest.query.get(request_id)
            if not request:
                return False
            
            student = User.query.get(request.student_id)
            alumni = User.query.get(request.alumni_id)

            print(f"Creating notification for alumni {alumni.id} about request from {student.full_name}")
            
            # Create in-app notification
            NotificationService.create_notification(
                user_id=alumni.id,
                sender_id=student.id,
                title="New Mentorship Request",
                message=f"{student.full_name} has sent you a mentorship request.",
                notification_type='mentorship_request',
                reference_id=request.id,
                reference_type='mentorship_request'
            )
            
            # Check email preferences
            prefs = NotificationPreference.query.filter_by(user_id=alumni.id).first()
            if prefs and prefs.email_mentorship_requests:
                # Send email
                subject = f"New Mentorship Request from {student.full_name}"
                html_content = f"""
                <h2>New Mentorship Request</h2>
                <p><strong>{student.full_name}</strong> has sent you a mentorship request.</p>
                <p><strong>Message:</strong> {request.message}</p>
                <p><a href="{os.getenv('APP_URL', 'http://localhost:5000')}/mentorship/requests/{request.id}" 
                      style="background-color: #667eea; color: white; padding: 10px 20px; 
                             text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Request
                </a></p>
                """
                NotificationService.send_email(alumni.email, subject, html_content)
            
            return True
        except Exception as e:
            print(f"Error in notify_mentorship_request: {str(e)}")
            return False
    
    @staticmethod
    def notify_mentorship_response(request_id, status):
        """Send notification when alumni responds to a mentorship request"""
        try:
            request = MentorshipRequest.query.get(request_id)
            if not request:
                return False
            
            student = User.query.get(request.student_id)
            alumni = User.query.get(request.alumni_id)
            
            status_text = "accepted" if status == 'accepted' else "declined"
            color = "#27ae60" if status == 'accepted' else "#e74c3c"
            
            # Create in-app notification
            NotificationService.create_notification(
                user_id=student.id,
                sender_id=alumni.id,
                title=f"Mentorship Request {status_text.title()}",
                message=f"{alumni.full_name} has {status_text} your mentorship request.",
                notification_type='mentorship_response',
                reference_id=alumni.id,
                reference_type='mentorship_request'
            )
            
            # Check email preferences
            prefs = NotificationPreference.query.filter_by(user_id=student.id).first()
            if prefs and prefs.email_mentorship_responses:
                # Send email
                subject = f"Mentorship Request {status_text.title()}"
                html_content = f"""
                <h2>Mentorship Request Update</h2>
                <p><strong>{alumni.full_name}</strong> has {status_text} your mentorship request.</p>
                <p><strong>Response:</strong> {request.response_message or 'No message provided'}</p>
                <p><a href="{os.getenv('APP_URL', 'http://localhost:5000')}/mentorship/requests/{request.id}" 
                      style="background-color: {color}; color: white; padding: 10px 20px; 
                             text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Details
                </a></p>
                """
                NotificationService.send_email(student.email, subject, html_content)
            
            return True
        except Exception as e:
            print(f"Error in notify_mentorship_response: {str(e)}")
            return False
    
    @staticmethod
    def notify_new_message(message_id):
        """Send notification when a new message is sent"""
        try:
            message = Message.query.get(message_id)
            if not message:
                return False
            
            # Get conversation to find recipient
            from ..models.user import Conversation
            conversation = Conversation.query.get(message.conversation_id)
            if not conversation:
                return False
            
            # Determine recipient
            recipient_id = conversation.alumni_id if message.sender_id == conversation.student_id else conversation.student_id
            sender = User.query.get(message.sender_id)
            recipient = User.query.get(recipient_id)
            
            # Create in-app notification
            NotificationService.create_notification(
                user_id=recipient.id,
                sender_id=sender.id,
                title="New Message",
                message=f"{sender.full_name} sent you a message.",
                notification_type='message',
                reference_id=message.id,
                reference_type='message'
            )
            
            # Check email preferences
            prefs = NotificationPreference.query.filter_by(user_id=recipient.id).first()
            if prefs and prefs.email_messages:
                # Send email (with quiet hours check)
                if NotificationService._is_within_quiet_hours(recipient.id):
                    return True  # Skip email during quiet hours
                
                subject = f"New Message from {sender.full_name}"
                html_content = f"""
                <h2>New Message</h2>
                <p><strong>{sender.full_name}</strong> sent you a message:</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    {message.message}
                </div>
                <p><a href="{os.getenv('APP_URL', 'http://localhost:5000')}/messages/{conversation.id}" 
                      style="background-color: #667eea; color: white; padding: 10px 20px; 
                             text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reply to Message
                </a></p>
                """
                NotificationService.send_email(recipient.email, subject, html_content)
            
            return True
        except Exception as e:
            print(f"Error in notify_new_message: {str(e)}")
            return False
    
    @staticmethod
    def notify_event_reminder(event_id):
        """Send reminders for upcoming events"""
        try:
            from ..models.user import Event, EventRegistration
            
            event = Event.query.get(event_id)
            if not event:
                return False
            
            # Get all registered users
            registrations = EventRegistration.query.filter_by(event_id=event_id, status='registered').all()
            
            for reg in registrations:
                user = User.query.get(reg.user_id)
                
                # Check preferences
                prefs = NotificationPreference.query.filter_by(user_id=user.id).first()
                if prefs and not prefs.email_event_reminders:
                    continue
                
                # Create in-app notification
                NotificationService.create_notification(
                    user_id=user.id,
                    title="Event Reminder",
                    message=f"Reminder: '{event.title}' is tomorrow at {event.start_date.strftime('%I:%M %p')}.",
                    notification_type='event_reminder',
                    reference_id=event.id,
                    reference_type='event'
                )
                
                # Send email
                subject = f"Reminder: {event.title} Tomorrow"
                html_content = f"""
                <h2>Event Reminder</h2>
                <p>This is a reminder that <strong>{event.title}</strong> is happening tomorrow.</p>
                <p><strong>Date:</strong> {event.start_date.strftime('%A, %B %d, %Y')}</p>
                <p><strong>Time:</strong> {event.start_date.strftime('%I:%M %p')} - {event.end_date.strftime('%I:%M %p')}</p>
                <p><strong>Location:</strong> {event.venue_name or 'Online Event'}</p>
                <p><a href="{os.getenv('APP_URL', 'http://localhost:5000')}/events/{event.id}" 
                      style="background-color: #667eea; color: white; padding: 10px 20px; 
                             text-decoration: none; border-radius: 5px; display: inline-block;">
                    View Event Details
                </a></p>
                """
                NotificationService.send_email(user.email, subject, html_content)
            
            return True
        except Exception as e:
            print(f"Error in notify_event_reminder: {str(e)}")
            return False
    
    @staticmethod
    def _is_within_quiet_hours(user_id):
        """Check if current time is within user's quiet hours"""
        prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
        if not prefs or not prefs.quiet_hours_enabled:
            return False
        
        now = datetime.now().time()
        start = datetime.strptime(prefs.quiet_hours_start, '%H:%M').time()
        end = datetime.strptime(prefs.quiet_hours_end, '%H:%M').time()
        
        if start <= end:
            return start <= now <= end
        else:  # Overnight
            return now >= start or now <= end
    
    @staticmethod
    def get_unread_count(user_id):
        """Get number of unread notifications for a user"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for n in notifications:
            n.mark_as_read()
        return True
    
    @staticmethod
    def create_default_preferences(user_id):
        """Create default notification preferences for a new user"""
        try:
            prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
            if not prefs:
                prefs = NotificationPreference(user_id=user_id)
                db.session.add(prefs)
                db.session.commit()
            return prefs
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default preferences: {str(e)}")
            return None
        
def update_request_status(request_id, status):
    """Updates status and notifies student ONLY if accepted."""
    try:
        req = MentorshipRequest.query.get(request_id)
        if not req:
            return None, "Request not found."

        if status not in ['accepted', 'rejected']:  # Changed to lowercase
            return None, "Invalid status. Use 'accepted' or 'rejected'."

        req.status = status
        from datetime import datetime
        req.response_date = datetime.utcnow()
        db.session.commit()

        return req, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)
    