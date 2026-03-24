from flask import Blueprint, request, jsonify, session, redirect, url_for
from ..models.user import User, ConnectionRequest, AlumniProfile
from ..config.db import db
from ..services.notification_service import NotificationService
from datetime import datetime

connection_bp = Blueprint('connection', __name__, url_prefix='/api/connections')

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@connection_bp.route('/request/<int:receiver_id>', methods=['POST'])
def send_connection_request(receiver_id):
    """Student sends connection request to alumni"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Check if receiver exists
    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already connected or request exists
    existing = ConnectionRequest.query.filter(
        ((ConnectionRequest.sender_id == current_user.id) & (ConnectionRequest.receiver_id == receiver_id)) |
        ((ConnectionRequest.sender_id == receiver_id) & (ConnectionRequest.receiver_id == current_user.id))
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            return jsonify({'error': 'Already connected'}), 400
        elif existing.status == 'pending':
            return jsonify({'error': 'Connection request already pending'}), 400
    
    # Create connection request
    data = request.get_json() or {}
    message = data.get('message', '')
    
    conn_request = ConnectionRequest(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message,
        status='pending'
    )
    db.session.add(conn_request)
    db.session.commit()
    
    # Send notification to receiver
    NotificationService.create_notification(
        user_id=receiver_id,
        sender_id=current_user.id,
        title="New Connection Request",
        message=f"{current_user.full_name} wants to connect with you",
        notification_type='connection_request',
        reference_id=conn_request.id,
        reference_type='connection'
    )
    
    return jsonify({
        'success': True,
        'message': 'Connection request sent',
        'request_id': conn_request.id
    }), 201

@connection_bp.route('/respond/<int:request_id>', methods=['POST'])
def respond_to_request(request_id):
    """Alumni accepts/rejects connection request"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn_request = ConnectionRequest.query.get_or_404(request_id)
    
    if conn_request.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    action = data.get('action') or request.form.get('action')
    
    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
    
    # ONLY update connection status - NO mentorship request created here
    conn_request.status = 'accepted' if action == 'accept' else 'rejected'
    conn_request.responded_at = datetime.utcnow()
    db.session.commit()
    
    # Send notification to sender (student)
    status_text = 'accepted' if action == 'accept' else 'declined'
    NotificationService.create_notification(
        user_id=conn_request.sender_id,
        sender_id=current_user.id,
        title=f"Connection Request {status_text.title()}",
        message=f"{current_user.full_name} has {status_text} your connection request",
        notification_type='connection_response',
        reference_id=conn_request.id,
        reference_type='connection'
    )
    
    return jsonify({
        'success': True,
        'message': f'Connection request {status_text}'
    })
    
    return jsonify({
        'success': True,
        'message': f'Connection request {status_text}'
    })

@connection_bp.route('/pending', methods=['GET'])
def get_pending_requests():
    """Get pending connection requests for current user"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Not logged in'}), 401
    
    pending = ConnectionRequest.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).all()
    
    result = []
    for req in pending:
        sender = User.query.get(req.sender_id)
        result.append({
            'id': req.id,
            'sender_id': req.sender_id,
            'sender_name': sender.full_name if sender else 'Unknown',
            'sender_role': sender.role if sender else 'unknown',
            'message': req.message,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(result)

@connection_bp.route('/my-connections', methods=['GET'])
def get_my_connections():
    """Get all accepted connections for current user"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Connections where user is sender and accepted
    sent = ConnectionRequest.query.filter_by(
        sender_id=current_user.id,
        status='accepted'
    ).all()
    
    # Connections where user is receiver and accepted
    received = ConnectionRequest.query.filter_by(
        receiver_id=current_user.id,
        status='accepted'
    ).all()
    
    connections = []
    
    for conn in sent:
        user = User.query.get(conn.receiver_id)
        if user:
            # Check if mentorship can be requested (alumni and available)
            can_request_mentorship = False
            if user.role == 'alumni':
                profile = AlumniProfile.query.filter_by(user_id=user.id).first()
                can_request_mentorship = profile and profile.mentorship_available
            
            connections.append({
                'id': user.id,
                'name': user.full_name,
                'role': user.role,
                'connected_since': conn.responded_at.strftime('%Y-%m-%d'),
                'can_request_mentorship': can_request_mentorship
            })
    
    for conn in received:
        user = User.query.get(conn.sender_id)
        if user:
            # Check if mentorship can be requested (alumni and available)
            can_request_mentorship = False
            if user.role == 'alumni':
                profile = AlumniProfile.query.filter_by(user_id=user.id).first()
                can_request_mentorship = profile and profile.mentorship_available
            
            connections.append({
                'id': user.id,
                'name': user.full_name,
                'role': user.role,
                'connected_since': conn.responded_at.strftime('%Y-%m-%d'),
                'can_request_mentorship': can_request_mentorship
            })
    
    return jsonify(connections)

@connection_bp.route('/check/<int:user_id>', methods=['GET'])
def check_connection_status(user_id):
    """Check connection status between current user and another user"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Check if they are the same user
    if current_user.id == user_id:
        return jsonify({'status': 'self'})
    
    # Check for existing connection
    connection = ConnectionRequest.query.filter(
        ((ConnectionRequest.sender_id == current_user.id) & (ConnectionRequest.receiver_id == user_id)) |
        ((ConnectionRequest.sender_id == user_id) & (ConnectionRequest.receiver_id == current_user.id))
    ).first()
    
    if not connection:
        return jsonify({'status': 'none'})
    
    return jsonify({
        'status': connection.status,
        'direction': 'sent' if connection.sender_id == current_user.id else 'received',
        'connection_id': connection.id
    })