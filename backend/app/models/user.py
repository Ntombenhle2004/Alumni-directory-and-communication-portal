from ..config.db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    profile_picture = db.Column(db.Text, default='default_avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    course = db.Column(db.String(100))
    graduation_year = db.Column(db.Integer)
    interests = db.Column(db.Text)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_expiry = db.Column(db.DateTime, nullable=True)

class AlumniProfile(db.Model):
    __tablename__ = 'alumni_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    job_title = db.Column(db.String(100))
    company = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    skills = db.Column(db.Text)
    graduation_year = db.Column(db.Integer)
    mentorship_available = db.Column(db.Boolean, default=True)
    rating_count = db.Column(db.Integer, default=0)

class MentorshipRequest(db.Model):
    __tablename__ = 'mentorship_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    alumni_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    status = db.Column(db.String(20), default='Pending') 
    message = db.Column(db.Text) 
    request_date = db.Column(db.DateTime, default=datetime.utcnow)   
    
    
class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    alumni_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text)
    message_type = db.Column(db.String(20), default='text') 
    file_path = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    action = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship('User', backref='admin_actions')
    
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False) 
    value = db.Column(db.String(100), nullable=False)     
    
class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    expiry_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', backref=db.backref('subscription', uselist=False))  
    
    
             