import requests
from ..models.user import Subscription, StudentProfile
from ..config.db import db
from datetime import datetime, timedelta

# 1. ALWAYS use the SECRET KEY (sk_test) for backend requests!
# Replace 'sk_test_your_actual_secret_key_here' with your real Secret Key from Paystack Dashboard
PAYSTACK_SECRET_KEY = "sk_test_bfac941a765302fb24a56bca110bcb0ac44434f3" 

def initialize_paystack_payment(email, amount_in_cents, user_id):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "email": email,
        "amount": amount_in_cents,
        "callback_url": "http://localhost:5000/api/payment/callback",
        "metadata": {
            "user_id": user_id  # <--- WITHOUT THIS, THE CALLBACK WON'T KNOW WHO PAID
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def verify_paystack_payment(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.get(url, headers=headers)
    res_data = response.json()
    
    if res_data.get('status') and res_data['data']['status'] == 'success':
        # Safely get user_id from the metadata we sent in Step 2
        user_id = res_data['data'].get('metadata', {}).get('user_id')
        return True, user_id
    return False, None

def activate_subscription_in_db(user_id):
    try:
        # 1. Update the StudentProfile
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            # If for some reason the profile is missing, we create it to prevent the crash
            profile = StudentProfile(user_id=user_id, is_subscribed=True)
            db.session.add(profile)
        else:
            profile.is_subscribed = True
        
        # 2. Update Subscription Table
        from ..models.user import Subscription
        sub = Subscription.query.filter_by(student_id=user_id).first()
        expiry = datetime.utcnow() + timedelta(days=30)
        
        if not sub:
            sub = Subscription(student_id=user_id, expiry_date=expiry, is_active=True)
            db.session.add(sub)
        else:
            sub.expiry_date = expiry
            sub.is_active = True
            
        db.session.flush() # Force the session to acknowledge changes
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)