from flask import render_template, current_app
from flask_mail import Mail, Message
import os


try:
    from flask_mail import Mail, Message
    MAIL_AVAILABLE = True
    print("✅ Flask-Mail loaded successfully")
except ImportError as e:
    print(f"⚠️ Flask-Mail not installed: {e}")
    MAIL_AVAILABLE = False
    class Mail:
        def init_app(self, app):
            pass
    class Message:
        def __init__(self, **kwargs):
            pass

mail = Mail()

def send_email(to_email, subject, template, **kwargs):
    """Send email using HTML template"""
    print(f"📧 [EMAIL DEBUG] Attempting to send email to: {to_email}")
    print(f"📧 [EMAIL DEBUG] Subject: {subject}")
    
    if not MAIL_AVAILABLE:
        print(f"❌ [EMAIL DEBUG] Flask-Mail not installed")
        return False
    
    try:
        with current_app.app_context():
           
            
            print(f"📧 [EMAIL DEBUG] Rendering template: emails/{template}.html")
            html_content = render_template(f'emails/{template}.html', **kwargs)
            text_content = render_template(f'emails/{template}.txt', **kwargs)
            
            msg = Message(
                subject=subject,
                recipients=[to_email],
                html=html_content,
                body=text_content,
                sender=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@alumniportal.com')
            )
            
            mail.send(msg)
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False
    

def send_mentorship_request_email(student, alumni, request):
    """Send email to alumni when a student requests mentorship"""
    subject = f"New Mentorship Request from {student.full_name}"
    return send_email(
        to_email=alumni.email,
        subject=subject,
        template='mentorship_request',
        student=student,
        alumni=alumni,
        request=request,
        app_url=os.getenv('APP_URL', 'http://localhost:5000')
    )

def send_mentorship_response_email(student, alumni, request, status):
    """Send email to student when alumni responds to mentorship request"""
    status_text = "accepted" if status == 'accepted' else "declined"
    subject = f"Mentorship Request {status_text.title()}"
    return send_email(
        to_email=student.email,
        subject=subject,
        template='mentorship_response',
        student=student,
        alumni=alumni,
        request=request,
        status=status,
        status_text=status_text,
        app_url=os.getenv('APP_URL', 'http://localhost:5000')
    )

def send_payment_initiated_email(student, alumni, request):
    """Send email to student when payment is initiated"""
    subject = "Payment Required to Start Mentorship"
    return send_email(
        to_email=student.email,
        subject=subject,
        template='payment_initiated',
        student=student,
        alumni=alumni,
        request=request,
        app_url=os.getenv('APP_URL', 'http://localhost:5000')
    )

def send_payment_success_email(student, alumni, request):
    """Send email to both student and alumni when payment is successful"""
    
    send_email(
        to_email=student.email,
        subject="Payment Successful - Mentorship Activated!",
        template='payment_success_student',
        student=student,
        alumni=alumni,
        request=request,
        app_url=os.getenv('APP_URL', 'http://localhost:5000')
    )
    
    