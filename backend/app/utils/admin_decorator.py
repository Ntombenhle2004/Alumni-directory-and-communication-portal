
from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('views.login_page'))
        
        from ..models.user import User
        user = User.query.get(session['user_id'])
        
        if not user or user.role != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('views.home'))
        
        return f(*args, **kwargs)
    return decorated_function