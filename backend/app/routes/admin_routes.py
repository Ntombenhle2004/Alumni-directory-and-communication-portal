from flask import Blueprint, jsonify, request
from ..services.admin_service import get_all_logs_logic, log_admin_action
from ..models.user import SystemSetting
from ..config.db import db

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/logs", methods=["GET"])
def view_audit_logs():
    """Fetches a list of all administrative actions taken."""
    logs, error = get_all_logs_logic()
    if error:
        return jsonify({"error": error}), 400
    
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "admin_name": log.admin.full_name if log.admin else "System/Unknown",
            "action": log.action,
            "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify(results), 200

@admin_bp.route("/admin/settings/price", methods=["POST"])
def update_price():
    data = request.get_json()
    admin_id = data.get("admin_id")
    new_price = data.get("price")  

    if not new_price:
        return jsonify({"error": "Price value is required"}), 400

    try:
        setting = SystemSetting.query.filter_by(key='sub_price').first()
        if not setting:
            setting = SystemSetting(key='sub_price', value=str(new_price))
            db.session.add(setting)
        else:
            setting.value = str(new_price)
        
        db.session.commit()
  
        log_admin_action(admin_id, f"Updated subscription price to R{int(new_price)/100}")
        
        return jsonify({"message": "Price updated successfully", "current_price": new_price}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/settings/price", methods=["GET"])
def get_admin_price():
    setting = SystemSetting.query.filter_by(key='sub_price').first()
    price = int(setting.value) if setting else 5000  
    return jsonify({
        "price_cents": price,
        "price_rand": price / 100,
        "display": f"R{price / 100:.2f}"
    }), 200