from ..models.user import AdminLog, User
from ..config.db import db

def log_admin_action(admin_id, action_text):
    """Helper function to record any admin action in the database."""
    try:
        new_log = AdminLog(admin_id=admin_id, action=action_text)
        db.session.add(new_log)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Logging Error: {e}")
        return False

def get_all_logs_logic():
    """Returns all logs from newest to oldest."""
    try:
        logs = AdminLog.query.order_by(AdminLog.created_at.desc()).all()
        return logs, None
    except Exception as e:
        return None, str(e)