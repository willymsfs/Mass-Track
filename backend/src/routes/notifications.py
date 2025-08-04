"""
Notifications routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from flask import Blueprint, request, jsonify
from src.auth import login_required
from src.models.notification import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """Get notifications for current user"""
    try:
        current_user = request.current_user
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        is_read = request.args.get('is_read')
        
        # Convert is_read to boolean if provided
        is_read_bool = None
        if is_read is not None:
            is_read_bool = is_read.lower() in ['true', '1', 'yes']
        
        result = Notification.find_by_priest(
            priest_id=current_user.id,
            is_read=is_read_bool,
            page=page,
            per_page=per_page
        )
        
        # Convert to dict format
        notifications_data = [Notification(**notification).to_dict() for notification in result['items']]
        
        return jsonify({
            'message': 'Notifications retrieved successfully',
            'data': notifications_data,
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'NOTIFICATIONS_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve notifications: {str(e)}'
            }
        }), 500

@notifications_bp.route('/<int:notification_id>', methods=['GET'])
@login_required
def get_notification(notification_id):
    """Get specific notification"""
    try:
        current_user = request.current_user
        
        notification = Notification.find_by_id(notification_id)
        if not notification:
            return jsonify({
                'error': {
                    'code': 'NOTIFICATION_NOT_FOUND',
                    'message': 'Notification not found'
                }
            }), 404
        
        # Check if user owns this notification
        if notification.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view your own notifications'
                }
            }), 403
        
        # Get additional details
        notification_data = notification.to_dict()
        
        # Add related entity details if available
        related_entity = notification.get_related_entity()
        if related_entity:
            notification_data['related_entity'] = related_entity
        
        return jsonify({
            'message': 'Notification retrieved successfully',
            'data': notification_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'NOTIFICATION_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve notification: {str(e)}'
            }
        }), 500

@notifications_bp.route('/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        current_user = request.current_user
        
        notification = Notification.find_by_id(notification_id)
        if not notification:
            return jsonify({
                'error': {
                    'code': 'NOTIFICATION_NOT_FOUND',
                    'message': 'Notification not found'
                }
            }), 404
        
        # Check if user owns this notification
        if notification.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only mark your own notifications as read'
                }
            }), 403
        
        success = notification.mark_as_read()
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'MARK_READ_FAILED',
                    'message': 'Failed to mark notification as read'
                }
            }), 500
        
        return jsonify({
            'message': 'Notification marked as read successfully',
            'data': notification.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'MARK_READ_ERROR',
                'message': f'Failed to mark notification as read: {str(e)}'
            }
        }), 500

@notifications_bp.route('/<int:notification_id>/mark-unread', methods=['POST'])
@login_required
def mark_notification_unread(notification_id):
    """Mark notification as unread"""
    try:
        current_user = request.current_user
        
        notification = Notification.find_by_id(notification_id)
        if not notification:
            return jsonify({
                'error': {
                    'code': 'NOTIFICATION_NOT_FOUND',
                    'message': 'Notification not found'
                }
            }), 404
        
        # Check if user owns this notification
        if notification.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only mark your own notifications as unread'
                }
            }), 403
        
        success = notification.mark_as_unread()
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'MARK_UNREAD_FAILED',
                    'message': 'Failed to mark notification as unread'
                }
            }), 500
        
        return jsonify({
            'message': 'Notification marked as unread successfully',
            'data': notification.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'MARK_UNREAD_ERROR',
                'message': f'Failed to mark notification as unread: {str(e)}'
            }
        }), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    try:
        current_user = request.current_user
        
        affected_count = Notification.mark_all_read(current_user.id)
        
        return jsonify({
            'message': f'{affected_count} notifications marked as read successfully',
            'data': {
                'affected_count': affected_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'MARK_ALL_READ_ERROR',
                'message': f'Failed to mark all notifications as read: {str(e)}'
            }
        }), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete notification"""
    try:
        current_user = request.current_user
        
        notification = Notification.find_by_id(notification_id)
        if not notification:
            return jsonify({
                'error': {
                    'code': 'NOTIFICATION_NOT_FOUND',
                    'message': 'Notification not found'
                }
            }), 404
        
        # Check if user owns this notification
        if notification.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only delete your own notifications'
                }
            }), 403
        
        success = notification.delete()
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'DELETION_FAILED',
                    'message': 'Failed to delete notification'
                }
            }), 500
        
        return jsonify({
            'message': 'Notification deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'NOTIFICATION_DELETION_ERROR',
                'message': f'Failed to delete notification: {str(e)}'
            }
        }), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    try:
        current_user = request.current_user
        
        unread_count = Notification.get_unread_count(current_user.id)
        
        return jsonify({
            'message': 'Unread count retrieved successfully',
            'data': {
                'unread_count': unread_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'UNREAD_COUNT_ERROR',
                'message': f'Failed to get unread count: {str(e)}'
            }
        }), 500

@notifications_bp.route('/urgent', methods=['GET'])
@login_required
def get_urgent_notifications():
    """Get urgent unread notifications"""
    try:
        current_user = request.current_user
        
        urgent_notifications = Notification.get_urgent_notifications(current_user.id)
        urgent_data = [notification.to_dict() for notification in urgent_notifications]
        
        return jsonify({
            'message': 'Urgent notifications retrieved successfully',
            'data': urgent_data,
            'count': len(urgent_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'URGENT_NOTIFICATIONS_ERROR',
                'message': f'Failed to retrieve urgent notifications: {str(e)}'
            }
        }), 500

@notifications_bp.route('', methods=['POST'])
@login_required
def create_notification():
    """Create new notification (for testing or manual creation)"""
    try:
        current_user = request.current_user
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Required fields
        notification_type = data.get('notification_type')
        title = data.get('title')
        message = data.get('message')
        
        if not all([notification_type, title, message]):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'notification_type, title, and message are required'
                }
            }), 400
        
        # Validate notification type
        if notification_type not in Notification.NOTIFICATION_TYPES:
            return jsonify({
                'error': {
                    'code': 'INVALID_NOTIFICATION_TYPE',
                    'message': f'Invalid notification type. Must be one of: {", ".join(Notification.NOTIFICATION_TYPES)}'
                }
            }), 400
        
        # Optional fields
        priority = data.get('priority', 'normal')
        scheduled_for = data.get('scheduled_for')
        related_entity_type = data.get('related_entity_type')
        related_entity_id = data.get('related_entity_id')
        
        # Validate priority
        if priority not in Notification.PRIORITIES:
            return jsonify({
                'error': {
                    'code': 'INVALID_PRIORITY',
                    'message': f'Invalid priority. Must be one of: {", ".join(Notification.PRIORITIES)}'
                }
            }), 400
        
        # Parse scheduled_for if provided
        scheduled_for_dt = None
        if scheduled_for:
            try:
                scheduled_for_dt = datetime.fromisoformat(scheduled_for.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_SCHEDULED_FOR',
                        'message': 'Invalid scheduled_for format. Use ISO 8601 format'
                    }
                }), 400
        
        # Create notification
        notification = Notification.create(
            priest_id=current_user.id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            scheduled_for=scheduled_for_dt,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
        
        if not notification:
            return jsonify({
                'error': {
                    'code': 'CREATION_FAILED',
                    'message': 'Failed to create notification'
                }
            }), 500
        
        return jsonify({
            'message': 'Notification created successfully',
            'data': notification.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'NOTIFICATION_CREATION_ERROR',
                'message': f'Failed to create notification: {str(e)}'
            }
        }), 500

