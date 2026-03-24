from ..config.db import db
from ..models.user import User, MentorshipRequest, Event, Post, Report, AdminLog, SystemSetting
from datetime import datetime, timedelta
import json

class AdminService:
    
    @staticmethod
    def get_dashboard_stats():
        """Get statistics for admin dashboard"""
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Basic counts
        total_users = User.query.count()
        total_alumni = User.query.filter_by(role='alumni').count()
        total_students = User.query.filter_by(role='student').count()
        
        # Mentorship stats
        active_mentorships = MentorshipRequest.query.filter_by(status='accepted').count()
        pending_mentorships = MentorshipRequest.query.filter_by(status='pending').count()
        
        # Event stats
        total_events = Event.query.count()
        upcoming_events = Event.query.filter(Event.start_date > now).count()
        
        # Post stats
        total_posts = Post.query.count()
        
        # Revenue stats (from mentorship payments)
        paid_mentorships = MentorshipRequest.query.filter_by(
            payment_status='paid'
        ).filter(MentorshipRequest.payment_date >= start_of_month).all()
        
        revenue_this_month = sum([m.payment_amount for m in paid_mentorships if m.payment_amount])
        
        # Recent users (last 5)
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        # User growth data for chart (last 6 months)
        months = []
        user_growth = []
        revenue_data = []
        
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30*i)
            month_start = datetime(month_date.year, month_date.month, 1)
            month_end = datetime(month_date.year, month_date.month + 1, 1) if month_date.month < 12 else datetime(month_date.year + 1, 1, 1)
            
            months.append(month_start.strftime('%b'))
            
            # Users created this month
            new_users = User.query.filter(
                User.created_at >= month_start,
                User.created_at < month_end
            ).count()
            user_growth.append(new_users)
            
            # Revenue this month
            month_revenue = sum([m.payment_amount for m in MentorshipRequest.query.filter(
                MentorshipRequest.payment_status == 'paid',
                MentorshipRequest.payment_date >= month_start,
                MentorshipRequest.payment_date < month_end
            ).all() if m.payment_amount])
            revenue_data.append(month_revenue)
        
        return {
            'total_users': total_users,
            'total_alumni': total_alumni,
            'total_students': total_students,
            'active_mentorships': active_mentorships,
            'pending_mentorships': pending_mentorships,
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'total_posts': total_posts,
            'revenue_this_month': revenue_this_month,
            'recent_users': recent_users,
            'months': months,
            'user_growth': user_growth,
            'revenue_data': revenue_data
        }
    
    @staticmethod
    def get_pending_reports_count():
        """Get count of pending reports"""
        return Report.query.filter_by(status='pending').count()
    
    @staticmethod
    def get_all_reports():
        """Get all reports"""
        return Report.query.order_by(Report.created_at.desc()).all()
    
    @staticmethod
    def get_pending_reports():
        """Get only pending reports"""
        return Report.query.filter_by(status='pending').order_by(Report.created_at.desc()).all()
    
    @staticmethod
    def resolve_report(report_id, admin_id):
        """Resolve a report"""
        report = Report.query.get(report_id)
        if report:
            report.status = 'resolved'
            report.resolved_at = datetime.utcnow()
            report.resolved_by = admin_id
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def dismiss_report(report_id):
        """Dismiss a report"""
        report = Report.query.get(report_id)
        if report:
            report.status = 'dismissed'
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def delete_report(report_id):
        """Delete a report"""
        report = Report.query.get(report_id)
        if report:
            db.session.delete(report)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_transactions():
        """Get all transactions from mentorship payments and event registrations"""
        transactions = []
        
        # Mentorship payments
        mentorship_payments = MentorshipRequest.query.filter(
            MentorshipRequest.payment_status == 'paid',
            MentorshipRequest.payment_date.isnot(None)
        ).order_by(MentorshipRequest.payment_date.desc()).all()
        
        for mp in mentorship_payments:
            user = User.query.get(mp.student_id)
            transactions.append({
                'id': f'M{mp.id}',
                'user': user,
                'type': 'mentorship',
                'amount': mp.payment_amount,
                'status': 'paid',
                'date': mp.payment_date,
                'reference': mp.payment_transaction_id
            })
        
        # Event registrations with payment
        from ..models.user import EventRegistration
        event_payments = EventRegistration.query.filter(
            EventRegistration.payment_status == 'paid',
            EventRegistration.payment_date.isnot(None)
        ).order_by(EventRegistration.payment_date.desc()).all()
        
        for ep in event_payments:
            user = User.query.get(ep.user_id)
            transactions.append({
                'id': f'E{ep.id}',
                'user': user,
                'type': 'event',
                'amount': ep.payment_amount,
                'status': 'paid',
                'date': ep.payment_date,
                'reference': ep.payment_transaction_id
            })
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return transactions
    
    @staticmethod
    def get_system_settings():
        """Get all system settings as a dictionary"""
        settings = SystemSetting.query.all()
        return {s.key: s.value for s in settings}
    
    @staticmethod
    def update_setting(key, value, admin_id):
        """Update a system setting"""
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            setting.updated_by = admin_id
        else:
            setting = SystemSetting(
                key=key,
                value=value,
                updated_by=admin_id
            )
            db.session.add(setting)
        db.session.commit()
        return setting

def log_admin_action(admin_id, action, target_id=None, details=None):
    """Log admin actions for audit trail"""
    try:
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_id=target_id,
            details=details or '',
            ip_address=None,  # Can be added from request
            created_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")
        db.session.rollback()