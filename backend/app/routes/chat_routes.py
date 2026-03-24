from flask import Blueprint, request, jsonify, session
from flask_mail import Message

from ..models.user import Conversation, Message, User
from ..services.chat_service import (
    get_chat_history, 
    start_conversation_logic, 
    send_message_logic,
    update_message_logic,
    delete_single_message,
    delete_entire_conversation
)

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat/start", methods=["POST"])
def start_chat():
    """Checks if a chat exists between student and alumni; if not, creates it."""
    data = request.get_json()
    conv, error = start_conversation_logic(data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({
        "conversation_id": conv.id,
        "student_id": conv.student_id,
        "alumni_id": conv.alumni_id
    }), 200


@chat_bp.route("/chat/send", methods=["POST"])
def send_message():
    """Sends text or a file link."""
    data = request.get_json()
    msg, error = send_message_logic(data)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Message sent", "id": msg.id}), 201


@chat_bp.route("/chat/history/<int:conv_id>/viewer/<int:user_id>", methods=["GET"])
def chat_history(conv_id, user_id):
    """
    Fetches messages. 
    If user_id is a non-subscribed student, files are 'LOCKED'.
    """
    history, error = get_chat_history(conv_id, user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify(history), 200

@chat_bp.route("/chat/message/<int:msg_id>", methods=["PUT"])
def edit_message(msg_id):
    data = request.get_json()
    user_id = data.get("user_id") 
    new_text = data.get("message")
    
    msg, error = update_message_logic(msg_id, user_id, new_text)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Message updated successfully"}), 200


@chat_bp.route("/chat/message/<int:msg_id>", methods=["DELETE"])
def delete_message(msg_id):
    user_id = request.args.get("user_id", type=int) 
    
    success, error = delete_single_message(msg_id, user_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Message deleted"}), 200

 
@chat_bp.route("/chat/conversation/<int:conv_id>", methods=["DELETE"])
def delete_chat(conv_id):
    success, error = delete_entire_conversation(conv_id)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Conversation and all messages cleared"}), 200

@chat_bp.route("/chat/my-conversations", methods=["GET"])
def get_my_conversations():
    """Get all conversations for the current user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    from ..models.user import User
    
    # Get conversations where user is either student or alumni
    conversations = Conversation.query.filter(
        (Conversation.student_id == user_id) | (Conversation.alumni_id == user_id)
    ).order_by(Conversation.created_at.desc()).all()
    
    result = []
    for conv in conversations:
        # Determine the other user
        other_id = conv.alumni_id if conv.student_id == user_id else conv.student_id
        other_user = User.query.get(other_id)
        
        # Get last message
        last_message = Message.query.filter_by(conversation_id=conv.id).order_by(Message.sent_at.desc()).first()
        
        result.append({
            'id': conv.id,
            'other_user_id': other_id,
            'other_user_name': other_user.full_name if other_user else 'Unknown',
            'last_message': last_message.message[:50] if last_message else None,
            'last_message_time': last_message.sent_at.strftime('%H:%M') if last_message else None
        })
    
    return jsonify(result), 200


