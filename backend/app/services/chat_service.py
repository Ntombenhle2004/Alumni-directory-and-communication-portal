# app/services/chat_service.py
from ..models.user import Conversation, Message, User, StudentProfile, MentorshipRequest
from ..config.db import db
from datetime import datetime

from ..models.user import Conversation, Message, User, StudentProfile, MentorshipRequest, Connection
from ..config.db import db
from datetime import datetime

def can_chat(user_id, other_id):
    """
    Return True if users are allowed to chat.
    Conditions:
    1. If both are alumni and connected (Connection accepted)
    2. If there's an accepted, paid mentorship between them
    """
    user = User.query.get(user_id)
    other = User.query.get(other_id)
    
    # Case 1: Both are alumni - check if they are connected
    if user.role == 'alumni' and other.role == 'alumni':
        connection = Connection.query.filter(
            ((Connection.user_id == user_id) & (Connection.connected_user_id == other_id)) |
            ((Connection.user_id == other_id) & (Connection.connected_user_id == user_id)),
            Connection.status == 'accepted'
        ).first()
        return connection is not None
    
    # Case 2: Mentorship relationship (student-alumni)
    req = MentorshipRequest.query.filter(
        ((MentorshipRequest.student_id == user_id) & (MentorshipRequest.alumni_id == other_id)) |
        ((MentorshipRequest.student_id == other_id) & (MentorshipRequest.alumni_id == user_id)),
        MentorshipRequest.status == 'accepted',
        MentorshipRequest.payment_status == 'paid'
    ).first()
    return req is not None


def start_conversation_logic(data):
    """Checks if a conversation exists; if not, creates one."""
    student_id = data.get('student_id')
    alumni_id = data.get('alumni_id')
    if not student_id or not alumni_id:
        return None, "Missing student_id or alumni_id"

    # Check if they are allowed to chat
    if not can_chat(student_id, alumni_id):
        return None, "You are not connected with this user. Please connect first to start a conversation."

    try:
        conv = Conversation.query.filter_by(student_id=student_id, alumni_id=alumni_id).first()
        if not conv:
            conv = Conversation(student_id=student_id, alumni_id=alumni_id)
            db.session.add(conv)
            db.session.commit()
        return conv, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to start conversation: {str(e)}"


def send_message_logic(data):
    """Sends a new message (text, image, or document)."""
    conversation_id = data.get('conversation_id')
    sender_id = data.get('sender_id')
    if not conversation_id or not sender_id:
        return None, "Missing conversation_id or sender_id"

    conv = Conversation.query.get(conversation_id)
    if not conv:
        return None, "Conversation not found"

    # Determine the other user
    other_id = conv.alumni_id if conv.student_id == sender_id else conv.student_id
    
    # Check if they are allowed to chat
    if not can_chat(sender_id, other_id):
        return None, "You are not connected with this user. Please connect first to send messages."

    try:
        new_msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            message=data.get("message"),
            message_type=data.get("message_type", "text"),
            file_path=data.get("file_path")
        )
        db.session.add(new_msg)
        db.session.commit()
        return new_msg, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to send message: {str(e)}"


def get_chat_history(conversation_id, viewer_id):
    """Fetch messages; check if viewer is allowed to view"""
    conv = Conversation.query.get(conversation_id)
    if not conv:
        return None, "Conversation not found"

    viewer = User.query.get(viewer_id)
    if not viewer:
        return None, "Viewer not found"

    # Determine the other user in the conversation
    other_id = conv.alumni_id if conv.student_id == viewer_id else conv.student_id

    # Check if they are allowed to chat
    if not can_chat(viewer_id, other_id):
        return None, "You do not have permission to view this conversation."

    try:
        messages = Message.query.filter_by(conversation_id=conversation_id)\
                                .order_by(Message.sent_at.asc()).all()

        # Check if viewer is premium (for file attachments)
        is_subscribed = False
        role = viewer.role.lower()
        if role in ['alumni', 'alumn', 'admin']:
            is_subscribed = True
        elif role == 'student':
            profile = StudentProfile.query.filter_by(user_id=viewer_id).first()
            if profile and profile.is_subscribed:
                is_subscribed = True

        output = []
        for m in messages:
            msg_data = {
                "id": m.id,
                "sender_id": m.sender_id,
                "text": m.message,
                "type": m.message_type,
                "sent_at": m.sent_at.strftime("%H:%M")
            }

            # Handle file attachments
            if m.message_type in ['image', 'document']:
                if is_subscribed:
                    msg_data["file_url"] = m.file_path
                else:
                    msg_data["file_url"] = "LOCKED"
                    msg_data["text"] = "🔒 Upgrade to Premium to view attachments"

            output.append(msg_data)
        return output, None
    except Exception as e:
        return None, f"Error: {str(e)}"


def update_message_logic(message_id, sender_id, new_text):
    try:
        msg = Message.query.get(message_id)
        if not msg or msg.sender_id != sender_id:
            return None, "Unauthorized or message not found."
        msg.message = new_text
        db.session.commit()
        return msg, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def delete_single_message(message_id, user_id):
    try:
        msg = Message.query.get(message_id)
        if not msg or msg.sender_id != user_id:
            return None, "Unauthorized or message not found."
        db.session.delete(msg)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def delete_entire_conversation(conversation_id):
    try:
        conv = Conversation.query.get(conversation_id)
        if not conv:
            return None, "Conversation not found."
        Message.query.filter_by(conversation_id=conversation_id).delete()
        db.session.delete(conv)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)