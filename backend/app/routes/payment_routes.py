from flask import Blueprint, redirect, request, jsonify, session, url_for

from ..services.notification_service import NotificationService

from ..services.email_service import send_payment_success_email, send_payment_initiated_email
from ..config.db import db                          # relative import
from ..models.user import SystemSetting, MentorshipRequest, User
from ..services.payment_service import (
    initialize_paystack_payment,
    verify_paystack_payment,
    activate_subscription_in_db
)
from datetime import datetime

payment_bp = Blueprint('payment', __name__)        

# (Keep all existing endpoints, but adjust as needed.)

@payment_bp.route("/subscribe/info", methods=["GET"])
def get_student_price_view():
    setting = SystemSetting.query.filter_by(key='sub_price').first()
    price = int(setting.value) if setting else 5000
    return jsonify({
        "plan": "Premium Access",
        "price_formatted": f"R{price / 100:.2f}",
        "cents": price
    }), 200

@payment_bp.route("/subscribe/pay", methods=["POST"])
def pay_subscription():
    data = request.get_json()
    email = data.get("email")
    user_id = data.get("user_id")

    if not email or not user_id:
        return jsonify({"error": "Email and User ID are required"}), 400

    setting = SystemSetting.query.filter_by(key='sub_price').first()
    amount = int(setting.value) if setting else 5000

    paystack_res = initialize_paystack_payment(email, amount, user_id)

    if not paystack_res.get('status'):
        return jsonify({"error": paystack_res.get('message', 'Paystack init failed')}), 400

    return jsonify(paystack_res), 200

@payment_bp.route("/subscribe/verify", methods=["POST"])
def verify_and_unlock():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    success, error = activate_subscription_in_db(user_id)

    if not success:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "Subscription is now ACTIVE.",
        "status": "Unlocked"
    }), 200

@payment_bp.route('/payment/callback', methods=['GET'])
def payment_callback():
    reference = request.args.get('reference')
    success, user_id = verify_paystack_payment(reference)

    if success and user_id:
        activated, error = activate_subscription_in_db(user_id)
        if activated:
            print(f"DEBUG: Activation successful for User {user_id}")
            return "<h1>Success!</h1><p>Subscription active. You can return to the app.</p>"
        else:
            print(f"DEBUG: Activation failed: {error}")
            return f"<h1>Activation Error</h1><p>{error}</p>", 500

    return "<h1>Verification Failed</h1>", 400

@payment_bp.route("/mentorship/initiate/<int:request_id>", methods=["POST"])
def initiate_mentorship_payment(request_id):
    """Student initiates payment for an accepted mentorship request."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    req = MentorshipRequest.query.get_or_404(request_id)
    if req.student_id != user_id:
        return jsonify({"error": "Not your request"}), 403
    if req.status != 'accepted':
        return jsonify({"error": "Mentorship not accepted yet"}), 400
    if req.payment_status == 'paid':
        return jsonify({"error": "Already paid"}), 400

    # Get student and alumni objects
    student = User.query.get(req.student_id)
    alumni = User.query.get(req.alumni_id)
    
    if not student or not alumni:
        return jsonify({"error": "User not found"}), 404

    # Get amount from request
    data = request.get_json() or {}
    amount = data.get('amount', 25000)  # Default to R250.00
    plan = data.get('plan', 'monthly')
    
    # Store plan in session metadata
    metadata = {
        'request_id': request_id, 
        'user_id': user_id,
        'plan': plan,
        'amount': amount
    }

    # Initialize payment
    from ..services.payment_service import initialize_paystack_payment
    
    response = initialize_paystack_payment(
        email=student.email,
        amount=amount,
        metadata=metadata
    )
    
    if not response.get('status'):
        return jsonify({"error": response.get('message', 'Payment initiation failed')}), 400

    # Store reference for verification
    req.payment_transaction_id = response['data']['reference']
    req.payment_status = 'pending'
    req.payment_amount = amount / 100  # Store in Rands
    db.session.commit()
    
    # Send email notification to student about payment initiation
    from ..services.email_service import send_payment_initiated_email
    send_payment_initiated_email(student, alumni, req)

    # Return the authorization URL
    return jsonify({
        'authorization_url': response['data']['authorization_url'],
        'reference': response['data']['reference']
    }), 200

@payment_bp.route("/mentorship/callback", methods=["GET"])
def mentorship_payment_callback():
    """Payment callback - verifies and completes payment."""
    reference = request.args.get('reference')
    
    if not reference:
        return "Missing reference", 400
    
    # Find the mentorship request by reference
    req = MentorshipRequest.query.filter_by(payment_transaction_id=reference).first()
    
    if not req:
        return "Request not found", 404
    
    # For demo/simulation, mark as paid directly
    req.payment_status = 'paid'
    req.payment_date = datetime.utcnow()
    db.session.commit()
    

    # Send notifications
    student = User.query.get(req.student_id)
    alumni = User.query.get(req.alumni_id)
    
    if student and alumni:
        # Send success notifications
        NotificationService.create_notification(
            user_id=req.alumni_id,
            title="Mentorship Payment Confirmed",
            message=f"The student has paid. You can now communicate.",
            notification_type='payment_success',
            reference_id=req.id,
            reference_type='mentorship'
        )
        NotificationService.create_notification(
            user_id=req.student_id,
            title="Payment Successful",
            message=f"Your payment was successful. You can now message your mentor.",
            notification_type='payment_success',
            reference_id=req.id,
            reference_type='mentorship'
        )
        
        # Send email notifications
        send_payment_success_email(student, alumni, req)
    
    return redirect(url_for('student.my_mentors'))

@payment_bp.route("/event/initiate/<int:event_id>", methods=["POST"])
def initiate_event_payment(event_id):
    """Student initiates payment for an event"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    from ..models.user import Event, EventRegistration, User
    
    event = Event.query.get_or_404(event_id)
    
    # Check if event has a price
    if event.price <= 0:
        return jsonify({"error": "This event is free"}), 400
    
    # Check if user is already registered
    existing = EventRegistration.query.filter_by(
        event_id=event_id,
        user_id=user_id
    ).first()
    
    if existing:
        if existing.payment_status == 'paid':
            return jsonify({"error": "Already registered and paid"}), 400
        elif existing.payment_status == 'pending':
            pass  
    # Get student
    student = User.query.get(user_id)
    
    # Get amount in cents
    amount = int(event.price * 100)
    
    # Initialize payment
    from ..services.payment_service import initialize_paystack_payment
    
    response = initialize_paystack_payment(
        email=student.email,
        amount=amount,
        metadata={
            'event_id': event_id,
            'user_id': user_id,
            'type': 'event'
        }
    )
    
    if not response.get('status'):
        return jsonify({"error": response.get('message', 'Payment initiation failed')}), 400
    
    # Create or update registration
    if existing:
        existing.payment_status = 'pending'
        existing.payment_transaction_id = response['data']['reference']
    else:
        registration = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            payment_status='pending',
            payment_amount=event.price,
            payment_transaction_id=response['data']['reference']
        )
        db.session.add(registration)
    
    db.session.commit()
    
    return jsonify({
        'authorization_url': response['data']['authorization_url'],
        'reference': response['data']['reference']
    }), 200

@payment_bp.route("/event/callback", methods=["GET"])
def event_payment_callback():
    """Payment callback for event payment"""
    reference = request.args.get('reference')
    
    if not reference:
        return "Missing reference", 400
    
    from ..models.user import EventRegistration, Event
    
    # Find the registration by reference
    registration = EventRegistration.query.filter_by(payment_transaction_id=reference).first()
    
    if not registration:
        return "Registration not found", 404
    
    # Mark as paid
    registration.payment_status = 'paid'
    registration.payment_date = datetime.utcnow()
    registration.status = 'registered'
    db.session.commit()
    
    # Send notification to user
    from ..services.notification_service import NotificationService
    NotificationService.create_notification(
        user_id=registration.user_id,
        title="Event Registration Confirmed",
        message=f"You have successfully registered for {registration.event.title}",
        notification_type='event_payment_success',
        reference_id=registration.event_id,
        reference_type='event'
    )
    
    # Send notification to event organizer
    if registration.event.organizer_id:
        NotificationService.create_notification(
            user_id=registration.event.organizer_id,
            title="New Event Registration",
            message=f"{registration.user.full_name} has registered for {registration.event.title}",
            notification_type='event_registration',
            reference_id=registration.event_id,
            reference_type='event'
        )
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registration Successful</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0; display: flex; align-items: center; justify-content: center; }
            .success-box { background: white; border-radius: 20px; padding: 40px; max-width: 500px; margin: 0 auto; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            h1 { color: #27ae60; margin-bottom: 20px; font-size: 2rem; }
            .checkmark { font-size: 4rem; color: #27ae60; margin-bottom: 20px; }
            p { color: #666; margin-bottom: 30px; line-height: 1.6; }
            .btn { display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: transform 0.2s; }
            .btn:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="success-box">
            <div class="checkmark">✅</div>
            <h1>Registration Successful!</h1>
            <p>Your event registration has been confirmed.</p>
            <p>You will receive a confirmation email shortly.</p>
            <a href="/events" class="btn">Browse More Events</a>
        </div>
        <script>
            setTimeout(function() {
                window.location.href = "/events";
            }, 3000);
        </script>
    </body>
    </html>
    """