"""
Dashboard routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from src.auth import login_required
from src.models.user import User
from src.models.mass_celebration import MassCelebration
from src.models.bulk_intention import BulkIntention
from src.models.monthly_obligation import MonthlyObligation
from src.models.notification import Notification

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('', methods=['GET'])
@login_required
def get_dashboard():
    """Get comprehensive dashboard data for current user"""
    try:
        current_user = request.current_user
        
        # Get basic dashboard data from user model
        dashboard_data = current_user.get_dashboard_data()
        
        # Enhance with additional dashboard information
        today = date.today()
        
        # Get today's celebrations
        today_celebrations = MassCelebration.get_today_celebrations(current_user.id)
        dashboard_data['today_celebrations'] = [celebration.to_dict() for celebration in today_celebrations]
        
        # Get this week's summary
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_result = MassCelebration.find_by_priest(
            priest_id=current_user.id,
            start_date=week_start,
            end_date=week_end,
            per_page=100
        )
        
        dashboard_data['this_week'] = {
            'total_masses': len(week_result['items']),
            'start_date': week_start.isoformat(),
            'end_date': week_end.isoformat()
        }
        
        # Get current month obligation
        current_month_obligation = MonthlyObligation.find_current_month(current_user.id)
        if current_month_obligation:
            dashboard_data['current_month_obligation'] = current_month_obligation.to_dict()
        else:
            # Create current month obligation if it doesn't exist
            now = datetime.now()
            current_month_obligation = MonthlyObligation.get_or_create(
                priest_id=current_user.id,
                year=now.year,
                month=now.month
            )
            dashboard_data['current_month_obligation'] = current_month_obligation.to_dict() if current_month_obligation else None
        
        # Get low count bulk intentions
        low_count_intentions = BulkIntention.get_low_count_intentions(
            priest_id=current_user.id,
            threshold=10
        )
        dashboard_data['low_count_bulk_intentions'] = [intention.to_dict() for intention in low_count_intentions]
        
        # Get urgent notifications
        urgent_notifications = Notification.get_urgent_notifications(current_user.id)
        dashboard_data['urgent_notifications'] = [notification.to_dict() for notification in urgent_notifications]
        
        # Get recent activity (last 7 days)
        recent_start = today - timedelta(days=7)
        recent_result = MassCelebration.find_by_priest(
            priest_id=current_user.id,
            start_date=recent_start,
            end_date=today,
            per_page=10
        )
        
        dashboard_data['recent_activity'] = {
            'celebrations': [MassCelebration(**celebration).to_dict() for celebration in recent_result['items'][:5]],
            'total_count': len(recent_result['items'])
        }
        
        return jsonify({
            'message': 'Dashboard data retrieved successfully',
            'data': dashboard_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DASHBOARD_ERROR',
                'message': f'Failed to retrieve dashboard data: {str(e)}'
            }
        }), 500

@dashboard_bp.route('/summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    """Get quick dashboard summary"""
    try:
        current_user = request.current_user
        
        # Get basic counts
        today = date.today()
        
        # Today's masses
        today_masses = len(MassCelebration.get_today_celebrations(current_user.id))
        
        # This month's masses
        month_start = today.replace(day=1)
        month_result = MassCelebration.find_by_priest(
            priest_id=current_user.id,
            start_date=month_start,
            end_date=today,
            per_page=1000
        )
        month_masses = len(month_result['items'])
        
        # Active bulk intentions
        active_bulk_intentions = BulkIntention.find_active_by_priest(current_user.id)
        
        # Unread notifications
        unread_notifications = Notification.get_unread_count(current_user.id)
        
        # Current month obligation
        current_month_obligation = MonthlyObligation.find_current_month(current_user.id)
        monthly_progress = {
            'completed': current_month_obligation.completed_count if current_month_obligation else 0,
            'target': current_month_obligation.target_count if current_month_obligation else 3,
            'percentage': current_month_obligation.get_completion_percentage() if current_month_obligation else 0
        }
        
        summary = {
            'today_masses': today_masses,
            'month_masses': month_masses,
            'active_bulk_intentions': len(active_bulk_intentions),
            'unread_notifications': unread_notifications,
            'monthly_progress': monthly_progress,
            'bulk_intentions_summary': [
                {
                    'id': intention.id,
                    'title': getattr(intention, 'intention_title', 'Unknown'),
                    'current_count': intention.current_count,
                    'total_count': intention.total_count,
                    'is_paused': intention.is_paused,
                    'status_level': intention.get_status_level()
                }
                for intention in active_bulk_intentions
            ]
        }
        
        return jsonify({
            'message': 'Dashboard summary retrieved successfully',
            'data': summary
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DASHBOARD_SUMMARY_ERROR',
                'message': f'Failed to retrieve dashboard summary: {str(e)}'
            }
        }), 500

@dashboard_bp.route('/statistics', methods=['GET'])
@login_required
def get_dashboard_statistics():
    """Get detailed statistics for dashboard"""
    try:
        current_user = request.current_user
        
        # Query parameters
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year:
            year = datetime.now().year
        
        statistics = {}
        
        if month:
            # Monthly statistics
            monthly_stats = MassCelebration.get_monthly_summary(current_user.id, year, month)
            user_monthly_stats = current_user.get_monthly_statistics(year, month)
            
            statistics = {
                'type': 'monthly',
                'year': year,
                'month': month,
                'celebrations': monthly_stats,
                'user_stats': user_monthly_stats
            }
        else:
            # Yearly statistics
            yearly_stats = MassCelebration.get_yearly_summary(current_user.id, year)
            
            # Get monthly breakdown for the year
            monthly_breakdown = []
            for m in range(1, 13):
                month_stats = MassCelebration.get_monthly_summary(current_user.id, year, m)
                monthly_breakdown.append({
                    'month': m,
                    'month_name': datetime(year, m, 1).strftime('%B'),
                    'total_masses': month_stats.get('total_masses', 0),
                    'personal_masses': month_stats.get('personal_masses', 0),
                    'bulk_masses': month_stats.get('bulk_masses', 0)
                })
            
            statistics = {
                'type': 'yearly',
                'year': year,
                'summary': yearly_stats,
                'monthly_breakdown': monthly_breakdown
            }
        
        return jsonify({
            'message': 'Dashboard statistics retrieved successfully',
            'data': statistics
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DASHBOARD_STATISTICS_ERROR',
                'message': f'Failed to retrieve dashboard statistics: {str(e)}'
            }
        }), 500

@dashboard_bp.route('/calendar', methods=['GET'])
@login_required
def get_dashboard_calendar():
    """Get calendar data for dashboard"""
    try:
        current_user = request.current_user
        
        # Query parameters
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # Validate month
        if not (1 <= month <= 12):
            return jsonify({
                'error': {
                    'code': 'INVALID_MONTH',
                    'message': 'Month must be between 1 and 12'
                }
            }), 400
        
        # Get month start and end dates
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get celebrations for the month
        celebrations_result = MassCelebration.find_by_priest(
            priest_id=current_user.id,
            start_date=month_start,
            end_date=month_end,
            per_page=1000
        )
        
        # Group celebrations by date
        calendar_data = {}
        for celebration_data in celebrations_result['items']:
            celebration = MassCelebration(**celebration_data)
            date_str = celebration.celebration_date.isoformat()
            
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            
            calendar_data[date_str].append({
                'id': celebration.id,
                'mass_time': celebration.mass_time.isoformat() if celebration.mass_time else None,
                'location': celebration.location,
                'celebration_type': celebration.get_celebration_type(),
                'is_bulk_mass': celebration.is_bulk_mass(),
                'is_personal_mass': celebration.is_personal_mass(),
                'serial_number': celebration.serial_number
            })
        
        # Get fixed date intentions for the month
        from src.models.mass_intention import MassIntention
        fixed_date_intentions = MassIntention.get_fixed_date_intentions(
            priest_id=current_user.id,
            start_date=month_start,
            end_date=month_end
        )
        
        # Add fixed date intentions to calendar
        for intention in fixed_date_intentions:
            if intention.fixed_date:
                date_str = intention.fixed_date.isoformat()
                
                if date_str not in calendar_data:
                    calendar_data[date_str] = []
                
                # Check if already celebrated
                celebrated = any(
                    celebration.get('celebration_type') == intention.intention_type
                    for celebration in calendar_data[date_str]
                )
                
                if not celebrated:
                    calendar_data[date_str].append({
                        'type': 'fixed_date_intention',
                        'intention_id': intention.id,
                        'title': intention.title,
                        'intention_type': intention.intention_type,
                        'is_celebrated': False
                    })
        
        return jsonify({
            'message': 'Calendar data retrieved successfully',
            'data': {
                'year': year,
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'calendar': calendar_data,
                'total_days_with_masses': len([date_str for date_str, events in calendar_data.items() 
                                             if any(event.get('id') for event in events)])
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DASHBOARD_CALENDAR_ERROR',
                'message': f'Failed to retrieve calendar data: {str(e)}'
            }
        }), 500

@dashboard_bp.route('/alerts', methods=['GET'])
@login_required
def get_dashboard_alerts():
    """Get alerts and warnings for dashboard"""
    try:
        current_user = request.current_user
        
        alerts = []
        
        # Check for overdue monthly obligations
        overdue_obligations = MonthlyObligation.get_incomplete_obligations(
            priest_id=current_user.id,
            months_back=3
        )
        
        for obligation in overdue_obligations:
            if obligation.is_overdue():
                alerts.append({
                    'type': 'warning',
                    'category': 'monthly_obligation',
                    'title': 'Overdue Monthly Obligation',
                    'message': f'You have {obligation.get_remaining_count()} personal masses remaining for {obligation.get_month_name()} {obligation.year}',
                    'priority': 'high',
                    'data': obligation.to_dict()
                })
        
        # Check for low count bulk intentions
        low_count_intentions = BulkIntention.get_low_count_intentions(
            priest_id=current_user.id,
            threshold=5
        )
        
        for intention in low_count_intentions:
            if intention.current_count <= 5:
                priority = 'urgent' if intention.current_count <= 2 else 'high'
                alerts.append({
                    'type': 'warning',
                    'category': 'bulk_intention',
                    'title': 'Low Bulk Intention Count',
                    'message': f'Bulk intention "{getattr(intention, "intention_title", "Unknown")}" has only {intention.current_count} masses remaining',
                    'priority': priority,
                    'data': intention.to_dict()
                })
        
        # Check for upcoming fixed date intentions
        from src.models.mass_intention import MassIntention
        upcoming_intentions = MassIntention.get_upcoming_fixed_dates(
            priest_id=current_user.id,
            days_ahead=7
        )
        
        for intention in upcoming_intentions:
            days_until = (intention.fixed_date - date.today()).days
            if days_until <= 3:
                priority = 'urgent' if days_until <= 1 else 'high'
                alerts.append({
                    'type': 'reminder',
                    'category': 'fixed_date',
                    'title': 'Upcoming Fixed Date Mass',
                    'message': f'"{intention.title}" is scheduled for {intention.fixed_date} ({days_until} days)',
                    'priority': priority,
                    'data': intention.to_dict()
                })
        
        # Check current month progress
        current_month_obligation = MonthlyObligation.find_current_month(current_user.id)
        if current_month_obligation and not current_month_obligation.is_completed():
            today = date.today()
            days_remaining = (date(today.year, today.month + 1, 1) - today).days if today.month < 12 else (date(today.year + 1, 1, 1) - today).days
            
            if days_remaining <= 7 and current_month_obligation.get_remaining_count() > 0:
                alerts.append({
                    'type': 'reminder',
                    'category': 'monthly_progress',
                    'title': 'Monthly Personal Masses Due Soon',
                    'message': f'You have {current_month_obligation.get_remaining_count()} personal masses remaining with {days_remaining} days left in the month',
                    'priority': 'high' if days_remaining <= 3 else 'normal',
                    'data': current_month_obligation.to_dict()
                })
        
        # Sort alerts by priority
        priority_order = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return jsonify({
            'message': 'Dashboard alerts retrieved successfully',
            'data': {
                'alerts': alerts,
                'total_count': len(alerts),
                'urgent_count': len([alert for alert in alerts if alert['priority'] == 'urgent']),
                'high_count': len([alert for alert in alerts if alert['priority'] == 'high'])
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DASHBOARD_ALERTS_ERROR',
                'message': f'Failed to retrieve dashboard alerts: {str(e)}'
            }
        }), 500

