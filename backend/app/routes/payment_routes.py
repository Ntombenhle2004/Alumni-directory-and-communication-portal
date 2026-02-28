from flask import Blueprint, request, jsonify
from ..models.user import SystemSetting
from ..services.payment_service import initialize_paystack_payment, activate_subscription_in_db

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

    setting = SystemSetting.query.filter_by(key='sub_price').first()
    amount = int(setting.value) if setting else 5000 

    paystack_res, error = initialize_paystack_payment(email, amount)
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify(paystack_res), 200

@payment_bp.route("/subscribe/verify", methods=["POST"])
def verify_and_unlock():
    """
    Call this endpoint after the student finishes paying on Paystack.
    It unlocks the 'is_subscribed' status in the database.
    """
    data = request.get_json()
    user_id = data.get("user_id") 

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    success, error = activate_subscription_in_db(user_id)
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify({
        "message": "Payment Verified! Subscription is now ACTIVE.",
        "status": "Unlocked"
    }), 200