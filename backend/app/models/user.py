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
    
class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    # Move ondelete inside the ForeignKey()
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    alumni_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    score = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # webinar, workshop, networking, social, etc.
    event_mode = db.Column(db.String(20), nullable=False)  # online, in-person, hybrid
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    online_link = db.Column(db.String(500), nullable=True)  # Zoom/Teams link for online events
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    organizer = db.relationship('User', backref='organized_events', foreign_keys=[organizer_id])
    capacity = db.Column(db.Integer, nullable=True)  # Maximum attendees (None = unlimited)
    price = db.Column(db.Float, default=0.0)  # 0.0 for free events
    image_url = db.Column(db.String(500), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attendees = db.relationship('EventRegistration', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.title}>'
    
    @property
    def registered_count(self):
        return len([r for r in self.attendees if r.status == 'registered'])
    
    @property
    def is_full(self):
        if self.capacity:
            return self.registered_count >= self.capacity
        return False
    
    @property
    def registration_available(self):
        if not self.is_published or self.status != 'upcoming':
            return False
        if self.registration_deadline and datetime.utcnow() > self.registration_deadline:
            return False
        if self.is_full:
            return False
        return True

class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='registered')  # registered, attended, cancelled, waitlisted
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, free, refunded
    payment_amount = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.DateTime, nullable=True)
    checked_in = db.Column(db.Boolean, default=False)
    check_in_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    user = db.relationship('User', backref='event_registrations')
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_registration'),)
    def __repr__(self):
        return f'<EventRegistration {self.event_id}:{self.user_id}>'