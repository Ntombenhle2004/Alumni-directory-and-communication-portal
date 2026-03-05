from flask import Blueprint, request, jsonify
from ..models.user import SystemSetting
from ..services.payment_service import (
    initialize_paystack_payment, 
    verify_paystack_payment, 
    activate_subscription_in_db
)

payment_bp = Blueprint("payment", __name__)

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
    user_id = data.get("user_id") # <--- Add this

    if not email or not user_id:
        return jsonify({"error": "Email and User ID are required"}), 400

    setting = SystemSetting.query.filter_by(key='sub_price').first()
    amount = int(setting.value) if setting else 5000 

    # Update this call to include user_id
    paystack_res = initialize_paystack_payment(email, amount, user_id)
    
    # Check if Paystack returned an error in their JSON
    if not paystack_res.get('status'):
        return jsonify({"error": paystack_res.get('message', 'Paystack init failed')}), 400
        
    return jsonify(paystack_res), 200

@payment_bp.route("/subscribe/verify", methods=["POST"])
def verify_and_unlock():
    data = request.get_json()
    user_id = data.get("user_id") 

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Note: activate_subscription_in_db returns (bool, error)
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