import requests
import os
from flask import request, url_for
from datetime import datetime

from ..services.email_service import send_email
from ..config.db import db
from ..models.user import Subscription, User, MentorshipRequest

def get_base_url():
    """Get base URL from environment or request context"""
    # For production, use environment variable
    app_url = os.getenv('APP_URL')
    if app_url:
        return app_url.rstrip('/')
    
    # For development, use request context
    try:
        return request.url_root.rstrip('/')
    except:
        return 'http://127.0.0.1:5000'

def initialize_paystack_payment(email, amount, metadata=None, user_id=None):
    """
    Initialize Paystack payment.
    
    Args:
        email: Customer email
        amount: Amount in cents (e.g., 5000 = R50.00)
        metadata: Optional dictionary with additional data
        user_id: Optional user ID (for backward compatibility)
    """
    secret_key = os.getenv('PAYSTACK_SECRET_KEY')
    if not secret_key:
        return {'status': False, 'message': 'Paystack secret key not configured'}
    
    # Prepare metadata
    meta = metadata or {}
    if user_id:
        meta['user_id'] = user_id
    
    base_url = get_base_url()
    
    # Determine callback URL
    if 'request_id' in meta:
        # Mentorship payment
        callback_url = f"{base_url}/api/mentorship/callback"
    else:
        # Subscription payment
        callback_url = f"{base_url}/api/payment/callback"

    if metadata and metadata.get('type') == 'event':
        callback_url = f"{base_url}/api/event/callback"
    elif metadata and metadata.get('request_id'):
        callback_url = f"{base_url}/api/mentorship/callback"
    else:
        callback_url = f"{base_url}/api/payment/callback"
    
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'email': email,
        'amount': amount,
        'callback_url': callback_url,
        'metadata': meta
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()
        
        if result.get('status'):
            print(f"✅ Payment initialized: {result['data']['authorization_url']}")
        else:
            print(f"❌ Payment init failed: {result.get('message')}")
        
        return result
    except Exception as e:
        print(f"❌ Paystack error: {str(e)}")
        return {'status': False, 'message': str(e)}

def verify_paystack_payment(reference):
    """
    Verify Paystack payment using reference.
    Returns: (success, user_id) for subscription, or (success, data) for mentorship
    """
    secret_key = os.getenv('PAYSTACK_SECRET_KEY')
    if not secret_key:
        return False, None
    
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {secret_key}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        result = response.json()
        
        if result.get('status'):
            data = result['data']
            print(f"✅ Payment verified: {reference}")
            print(f"   Amount: {data['amount'] / 100:.2f} ZAR")
            print(f"   Metadata: {data.get('metadata')}")
            
            # Extract user_id from metadata
            metadata = data.get('metadata', {})
            user_id = metadata.get('user_id')
            
            return True, {
                'user_id': user_id,
                'amount': data['amount'],
                'reference': reference,
                'metadata': metadata
            }
        else:
            print(f"❌ Payment verification failed: {result.get('message')}")
            return False, None
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False, None

def activate_subscription_in_db(user_id):
    """
    Activate subscription for a user after successful payment.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        # Check if subscription already exists
        existing = Subscription.query.filter_by(student_id=user_id).first()
        
        if existing:
            # Update existing
            from datetime import datetime, timedelta
            existing.expiry_date = datetime.utcnow() + timedelta(days=30)
            existing.is_active = True
            existing.last_payment_date = datetime.utcnow()
        else:
            # Create new subscription
            from datetime import datetime, timedelta
            subscription = Subscription(
                student_id=user_id,
                expiry_date=datetime.utcnow() + timedelta(days=30),
                is_active=True,
                last_payment_date=datetime.utcnow()
            )
            db.session.add(subscription)
        
        # Update student profile subscription status
        from ..models.user import StudentProfile
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.is_subscribed = True
            profile.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        
        db.session.commit()
        print(f"✅ Subscription activated for {user.full_name}")
        return True, None
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error activating subscription: {str(e)}")
        return False, str(e)

def complete_mentorship_payment(request_id):
    """
    Mark mentorship request as paid after successful payment.
    """
    try:
        req = MentorshipRequest.query.get(request_id)
        if not req:
            return False, "Request not found"
        
        req.payment_status = 'paid'
        req.payment_date = datetime.utcnow()
        db.session.commit()
        
        print(f"✅ Mentorship payment completed for request {request_id}")
        return True, None
        
    except Exception as e:
        db.session.recording()
        return False, str(e)
    
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