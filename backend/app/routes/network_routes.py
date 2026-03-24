from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from ..config.db import db
from ..models.user import User, Connection, Post, PostLike, PostComment, Notification
from ..services.notification_service import NotificationService
from datetime import datetime
import os
from werkzeug.utils import secure_filename

network_bp = Blueprint("network", __name__, url_prefix="/network")

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ==================== CONNECTIONS ====================

@network_bp.route("/connections")
def connections():
    """View connections page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    # Get accepted connections
    accepted_connections = Connection.query.filter(
        ((Connection.user_id == user.id) | (Connection.connected_user_id == user.id)),
        Connection.status == 'accepted'
    ).all()
    
    # Get pending requests sent by user
    sent_requests = Connection.query.filter_by(
        user_id=user.id,
        status='pending'
    ).all()
    
    # Get pending requests received by user
    received_requests = Connection.query.filter_by(
        connected_user_id=user.id,
        status='pending'
    ).all()
    
    # Get suggested connections (alumni not yet connected)
    connected_ids = [user.id]
    for conn in accepted_connections:
        if conn.user_id == user.id:
            connected_ids.append(conn.connected_user_id)
        else:
            connected_ids.append(conn.user_id)
    
    # Also exclude those with pending requests
    for req in sent_requests:
        connected_ids.append(req.connected_user_id)
    for req in received_requests:
        connected_ids.append(req.user_id)
    
    suggested = User.query.filter(
        User.role == 'alumni',
        User.id != user.id,
        User.id.notin_(connected_ids)
    ).limit(10).all()
    
    return render_template("network/connections.html", 
                         user=user,
                         accepted_connections=accepted_connections,
                         sent_requests=sent_requests,
                         received_requests=received_requests,
                         suggested=suggested)


@network_bp.route("/connect/<int:user_id>", methods=["POST"])
def send_connection_request(user_id):
    """Send a connection request to another alumni"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Not logged in"}), 401
    
    if current_user.id == user_id:
        return jsonify({"error": "Cannot connect to yourself"}), 400
    
    # Check if connection already exists
    existing = Connection.query.filter(
        ((Connection.user_id == current_user.id) & (Connection.connected_user_id == user_id)) |
        ((Connection.user_id == user_id) & (Connection.connected_user_id == current_user.id))
    ).first()
    
    if existing:
        return jsonify({"error": "Connection request already exists"}), 400
    
    connection = Connection(
        user_id=current_user.id,
        connected_user_id=user_id,
        status='pending'
    )
    db.session.add(connection)
    db.session.commit()
    
    # Send notification
    NotificationService.create_notification(
        user_id=user_id,
        sender_id=current_user.id,
        title="New Connection Request",
        message=f"{current_user.full_name} wants to connect with you",
        notification_type='connection_request',
        reference_id=connection.id,
        reference_type='connection'
    )
    
    return jsonify({"success": True, "message": "Connection request sent"}), 200

@network_bp.route("/accept/<int:connection_id>", methods=["POST"])
def accept_connection(connection_id):
    """Accept a connection request"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Not logged in"}), 401
    
    connection = Connection.query.get_or_404(connection_id)
    if connection.connected_user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    connection.status = 'accepted'
    connection.accepted_at = datetime.utcnow()
    db.session.commit()
    
    # Send notification
    NotificationService.create_notification(
        user_id=connection.user_id,
        sender_id=current_user.id,
        title="Connection Request Accepted",
        message=f"{current_user.full_name} accepted your connection request",
        notification_type='connection_accepted',
        reference_id=connection.id,
        reference_type='connection'
    )
    
    return jsonify({"success": True, "message": "Connection accepted"}), 200

@network_bp.route("/reject/<int:connection_id>", methods=["POST"])
def reject_connection(connection_id):
    """Reject a connection request"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Not logged in"}), 401
    
    connection = Connection.query.get_or_404(connection_id)
    if connection.connected_user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    db.session.delete(connection)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Connection rejected"}), 200

# ==================== POSTS ====================

@network_bp.route("/feed")
def feed():
    """View network feed (posts from connections)"""
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    # Get IDs of connected users
    connections = Connection.query.filter(
        ((Connection.user_id == user.id) | (Connection.connected_user_id == user.id)),
        Connection.status == 'accepted'
    ).all()
    
    connected_ids = [user.id]
    for conn in connections:
        if conn.user_id == user.id:
            connected_ids.append(conn.connected_user_id)
        else:
            connected_ids.append(conn.user_id)
    
    # Get posts from connections and user's own posts
    posts = Post.query.filter(
        Post.author_id.in_(connected_ids),
        Post.visibility.in_(['public', 'connections'])
    ).order_by(Post.created_at.desc()).all()
    
    return render_template("network/feed.html", user=user, posts=posts)

@network_bp.route("/post", methods=["POST"])
def create_post():
    """Create a new post"""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    content = request.form.get('content')
    if not content:
        flash('Post content is required', 'error')
        return redirect(url_for('network.feed'))
    
    media_url = None
    media_type = 'text'
    
    # Handle file upload
    if 'media' in request.files:
        file = request.files['media']
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(upload_dir, exist_ok=True)
            unique_filename = f"{datetime.utcnow().timestamp()}_{filename}"
            file_path = f'/static/uploads/posts/{unique_filename}'
            file.save(os.path.join(upload_dir, unique_filename))
            media_url = file_path
            
            # Determine media type
            if file.content_type and file.content_type.startswith('image'):
                media_type = 'image'
            elif file.content_type and file.content_type.startswith('video'):
                media_type = 'video'
    
    # Handle link
    link_url = request.form.get('link_url')
    link_title = request.form.get('link_title')
    visibility = request.form.get('visibility', 'connections')
    
    post = Post(
        author_id=user.id,
        content=content,
        media_url=media_url,
        media_type=media_type,
        link_url=link_url,
        link_title=link_title,
        visibility=visibility
    )
    db.session.add(post)
    db.session.commit()
    
    flash('Post created successfully!', 'success')
    return redirect(url_for('network.feed'))

@network_bp.route("/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    """Like a post"""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    existing = PostLike.query.filter_by(post_id=post_id, user_id=user.id).first()
    
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        like = PostLike(post_id=post_id, user_id=user.id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    # Get updated like count
    like_count = PostLike.query.filter_by(post_id=post_id).count()
    
    return jsonify({"liked": liked, "likes_count": like_count}), 200

@network_bp.route("/post/<int:post_id>/comment", methods=["POST"])
def comment_on_post(post_id):
    """Add a comment to a post"""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    content = request.form.get('content')
    if not content:
        return jsonify({"error": "Comment content is required"}), 400
    
    comment = PostComment(
        post_id=post_id,
        user_id=user.id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    
    # Send notification to post author
    post = Post.query.get(post_id)
    if post.author_id != user.id:
        NotificationService.create_notification(
            user_id=post.author_id,
            sender_id=user.id,
            title="New Comment",
            message=f"{user.full_name} commented on your post: {content[:50]}...",
            notification_type='comment',
            reference_id=post_id,
            reference_type='post'
        )
    
    return jsonify({
        "success": True,
        "comment": {
            "id": comment.id,
            "user_name": user.full_name,
            "user_avatar": user.full_name[:2].upper(),
            "content": content,
            "created_at": comment.created_at.strftime('%b %d, %Y at %I:%M %p')
        }
    }), 200

@network_bp.route("/alumni-directory")
def alumni_directory():
    """Browse all alumni"""
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    # Get all alumni
    alumni = User.query.filter_by(role='alumni').all()
    
    # Get connection status for each
    for alum in alumni:
        if alum.id == user.id:
            alum.connection_status = 'self'
        else:
            connection = Connection.query.filter(
                ((Connection.user_id == user.id) & (Connection.connected_user_id == alum.id)) |
                ((Connection.user_id == alum.id) & (Connection.connected_user_id == user.id))
            ).first()
            if connection:
                alum.connection_status = connection.status
            else:
                alum.connection_status = 'none'
    
    return render_template("network/alumni_directory.html", user=user, alumni=alumni)