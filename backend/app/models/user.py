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
    student = db.relationship('User', foreign_keys=[student_id], backref='sent_mentorship_requests')
    alumni = db.relationship('User', foreign_keys=[alumni_id], backref='received_mentorship_requests') 
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, pending, paid, failed
    payment_amount = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_transaction_id = db.Column(db.String(100), nullable=True)
    response_date = db.Column(db.DateTime, nullable=True)  # Add this field
    response_message = db.Column(db.Text, nullable=True)
    
    
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # message, mentorship_request, mentorship_response, event_reminder, etc.
    
    # Reference to related entities
    reference_id = db.Column(db.Integer, nullable=True)
    reference_type = db.Column(db.String(50), nullable=True)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    @property
    def time_ago(self):
        diff = datetime.utcnow() - self.created_at
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Email notification preferences
    email_messages = db.Column(db.Boolean, default=True)
    email_mentorship_requests = db.Column(db.Boolean, default=True)
    email_mentorship_responses = db.Column(db.Boolean, default=True)
    email_event_reminders = db.Column(db.Boolean, default=True)
    email_event_updates = db.Column(db.Boolean, default=True)
    email_weekly_digest = db.Column(db.Boolean, default=False)
    
    # In-app notification preferences
    inapp_messages = db.Column(db.Boolean, default=True)
    inapp_mentorship_requests = db.Column(db.Boolean, default=True)
    inapp_mentorship_responses = db.Column(db.Boolean, default=True)
    inapp_event_reminders = db.Column(db.Boolean, default=True)
    inapp_event_updates = db.Column(db.Boolean, default=True)
    
    # Reminder settings
    reminder_days_before = db.Column(db.Integer, default=1)
    reminder_time = db.Column(db.String(5), default='09:00')
    
    # Quiet hours
    quiet_hours_enabled = db.Column(db.Boolean, default=False)
    quiet_hours_start = db.Column(db.String(5), nullable=True)
    quiet_hours_end = db.Column(db.String(5), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notification_preferences')
    
    def __repr__(self):
        return f'<NotificationPreference for user {self.user_id}>'


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  
    event_mode = db.Column(db.String(20), nullable=False)  
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)

    venue_name =db.Column(db.String(200), nullable =True)
    venue_address = db.Column(db.String(200))
    venue_capacity = db.Column(db.Integer, nullable= True)

    online_platform =db.Column(db.String(50), nullable=True)
    online_link = db.Column(db.String(500), nullable=True)
    Meeting_id = db.Column(db.String(100), nullable=True)
    meeting_password = db.Column(db.String(100), nullable=True)
    dial_in_numbers = db.Column(db.String(500), nullable=True)

    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    organizer = db.relationship('User', backref='organized_events', foreign_keys=[organizer_id])

    capacity = db.Column(db.Integer, nullable=True)  # Maximum attendees (None = unlimited)
    price = db.Column(db.Float, default=0.0)  # 0.0 for free events
    image_url = db.Column(db.String(500), nullable=True)

    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='upcoming') 
    
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
    payment_method = db.Column(db.String(50), nullable=True)
    payment_transaction_id = db.Column(db.String(100), nullable=True)
    checked_in = db.Column(db.Boolean, default=False)
    check_in_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    user = db.relationship('User', backref='event_registrations')
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_registration'),)
    def __repr__(self):
        return f'<EventRegistration {self.event_id}:{self.user_id}>'
    
class ConnectionRequest(db.Model):
    __tablename__ = 'connection_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_connections')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_connections')
    
    __table_args__ = (db.UniqueConstraint('sender_id', 'receiver_id', name='unique_connection'),)
    
    def __repr__(self):
        return f'<Connection {self.sender_id} -> {self.receiver_id}>'
    

class MentorResource(db.Model):
    __tablename__ = 'mentor_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    alumni_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)  # URL to uploaded file
    file_type = db.Column(db.String(50), nullable=True)  # pdf, video, link, etc.
    resource_type = db.Column(db.String(50), nullable=False, default='document')  # document, video, link, assignment
    external_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Who can access (all mentees or specific ones)
    is_public = db.Column(db.Boolean, default=True)  # True = all mentees, False = specific
    mentee_ids = db.Column(db.Text, nullable=True)  # Comma-separated list of mentee IDs
    
    # Relationships
    alumni = db.relationship('User', backref='mentor_resources')
    
    def __repr__(self):
        return f'<MentorResource {self.title}>'
    
class MentorshipSession(db.Model):
    __tablename__ = 'mentorship_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    mentorship_request_id = db.Column(db.Integer, db.ForeignKey('mentorship_requests.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Session timing
    session_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)  # Duration in minutes
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    
    # Meeting details
    meeting_link = db.Column(db.String(500), nullable=True)  # Zoom/Teams link
    meeting_platform = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(200), nullable=True)  # For in-person sessions
    
    # Resources
    resources = db.relationship('SessionResource', backref='session', lazy=True, cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    mentorship_request = db.relationship('MentorshipRequest', backref='sessions')
    
    def __repr__(self):
        return f'<MentorshipSession {self.title}>'

class SessionResource(db.Model):
    __tablename__ = 'session_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('mentorship_sessions.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)  # URL to uploaded file
    resource_type = db.Column(db.String(50), default='document')  # document, video, link, assignment
    external_link = db.Column(db.String(500), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SessionResource {self.title}>'

class Connection(db.Model):
    """Alumni to Alumni connections"""
    __tablename__ = 'connections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    connected_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='connection_requests')
    connected_user = db.relationship('User', foreign_keys=[connected_user_id], backref='accepted_connections')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'connected_user_id', name='unique_connection'),)
    
    def __repr__(self):
        return f'<Connection {self.user_id} -> {self.connected_user_id}>'

class Post(db.Model):
    """Posts/Stories from alumni"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(500), nullable=True)  # Image/video URL
    media_type = db.Column(db.String(20), default='text')  # text, image, video, link
    link_url = db.Column(db.String(500), nullable=True)   # External link
    link_title = db.Column(db.String(200), nullable=True)
    visibility = db.Column(db.String(20), default='connections')  # public, connections, private
    is_announcement = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='posts')
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.id} by {self.author_id}>'
    
    @property
    def likes_count(self):
        return len(self.likes)
    
    @property
    def comments_count(self):
        return len(self.comments)

class PostLike(db.Model):
    """Likes on posts"""
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_like'),)
    
    user = db.relationship('User', backref='post_likes')

class PostComment(db.Model):
    """Comments on posts"""
    __tablename__ = 'post_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='post_comments')