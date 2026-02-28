import requests
from ..models.user import Subscription, StudentProfile
from ..config.db import db
from datetime import datetime, timedelta

PAYSTACK_SECRET_KEY = "pk_test_c0ea551fdff3be438351f76cab4881c2440a3bc1"

def initialize_paystack_payment(email, amount_in_cents):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "email": email,
        "amount": amount_in_cents,
        "callback_url": "http://localhost:3000/payment-success" 
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json(), None

def activate_subscription_in_db(user_id):
    """This function flips the switch from 'Locked' to 'Unlocked'"""
    try:

        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.is_subscribed = True

        sub = Subscription.query.filter_by(student_id=user_id).first()
        expiry = datetime.utcnow() + timedelta(days=30)
        
        if not sub:
            sub = Subscription(student_id=user_id, expiry_date=expiry)
            db.session.add(sub)
        else:
            sub.expiry_date = expiry
            sub.is_active = True
            
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)