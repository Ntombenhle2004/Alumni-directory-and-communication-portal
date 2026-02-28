from ..models.user import Conversation, Message, User, StudentProfile
from ..config.db import db
from datetime import datetime

def start_conversation_logic(data):
    """Checks if a conversation exists; if not, creates one."""
    try:
        s_id = data.get("student_id")
        a_id = data.get("alumni_id")
        
        if not s_id or not a_id:
            return None, "Missing student_id or alumni_id"

        conv = Conversation.query.filter_by(student_id=s_id, alumni_id=a_id).first()
        
        if not conv:
            conv = Conversation(student_id=s_id, alumni_id=a_id)
            db.session.add(conv)
            db.session.commit()
            
        return conv, None
    except Exception as e:
        db.session.rollback()
        return None, f"Failed to start conversation: {str(e)}"

def send_message_logic(data):
    """Sends a new message (text, image, or document)."""
    try:
        new_msg = Message(
            conversation_id=data.get("conversation_id"),
            sender_id=data.get("sender_id"),
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
    """Fetches messages and applies the paywall logic for students."""
    try:
        viewer = User.query.get(viewer_id)
        if not viewer:
            return None, "Viewer not found"

        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.sent_at.asc()).all()

        is_subscribed = False
        if viewer.role.lower() == 'student':
            profile = StudentProfile.query.filter_by(user_id=viewer_id).first()
            is_subscribed = profile.is_subscribed if profile else False

        output = []
        for m in messages:
            msg_data = {
                "id": m.id,
                "sender_id": m.sender_id,
                "text": m.message,
                "type": m.message_type,
                "sent_at": m.sent_at.strftime("%H:%M")
            }


            if m.message_type in ['image', 'document']:
             
                if viewer.role.lower() in ['alumni', 'alumn'] or is_subscribed:
                    msg_data["file_url"] = m.file_path
                else:
                    msg_data["file_url"] = "LOCKED"
                    msg_data["text"] = " Upgrade to view attachment"

            output.append(msg_data)
            
        return output, None
    except Exception as e:
        return None, str(e)


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