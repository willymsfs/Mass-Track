"""
Users routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from flask import Blueprint, request, jsonify
from src.auth import login_required, admin_required
from src.models.user import User

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@admin_required
def get_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        result = User.get_all(page=page, per_page=per_page)
        
        # Convert users to dict
        users_data = [User(**user).to_dict() for user in result['items']]
        
        return jsonify({
            'message': 'Users retrieved successfully',
            'data': users_data,
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'USERS_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve users: {str(e)}'
            }
        }), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Get user by ID"""
    try:
        current_user = request.current_user
        
        # Users can only view their own profile unless they're admin
        if current_user.id != user_id:
            # For now, all authenticated users can view other profiles
            # This can be restricted later with proper role management
            pass
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        return jsonify({
            'message': 'User retrieved successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'USER_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve user: {str(e)}'
            }
        }), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user information"""
    try:
        current_user = request.current_user
        
        # Users can only update their own profile
        if current_user.id != user_id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only update your own profile'
                }
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Fields that can be updated
        updatable_fields = [
            'full_name', 'email', 'current_assignment', 'diocese', 
            'province', 'phone', 'address', 'profile_image_url', 'preferences'
        ]
        
        update_data = {k: v for k, v in data.items() if k in updatable_fields}
        
        if not update_data:
            return jsonify({
                'error': {
                    'code': 'NO_UPDATE_DATA',
                    'message': 'No valid fields to update'
                }
            }), 400
        
        # Check if email is being changed and if it already exists
        if 'email' in update_data and update_data['email'] != user.email:
            existing_email = User.find_by_email(update_data['email'])
            if existing_email:
                return jsonify({
                    'error': {
                        'code': 'EMAIL_EXISTS',
                        'message': 'Email already exists'
                    }
                }), 409
        
        # Update user
        success = user.update(**update_data)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update user'
                }
            }), 500
        
        return jsonify({
            'message': 'User updated successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'USER_UPDATE_ERROR',
                'message': f'Failed to update user: {str(e)}'
            }
        }), 500

@users_bp.route('/<int:user_id>/dashboard', methods=['GET'])
@login_required
def get_user_dashboard(user_id):
    """Get dashboard data for user"""
    try:
        current_user = request.current_user
        
        # Users can only view their own dashboard
        if current_user.id != user_id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view your own dashboard'
                }
            }), 403
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        dashboard_data = user.get_dashboard_data()
        
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

@users_bp.route('/<int:user_id>/statistics', methods=['GET'])
@login_required
def get_user_statistics(user_id):
    """Get statistics for user"""
    try:
        current_user = request.current_user
        
        # Users can only view their own statistics
        if current_user.id != user_id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view your own statistics'
                }
            }), 403
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get query parameters
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if month and not year:
            from datetime import datetime
            year = datetime.now().year
        
        if year and month:
            # Monthly statistics
            stats = user.get_monthly_statistics(year, month)
            stats_type = 'monthly'
        elif year:
            # Yearly statistics
            stats = user.get_yearly_statistics(year)
            stats_type = 'yearly'
        else:
            # Current month statistics
            from datetime import datetime
            now = datetime.now()
            stats = user.get_monthly_statistics(now.year, now.month)
            stats_type = 'current_month'
        
        return jsonify({
            'message': f'{stats_type.title()} statistics retrieved successfully',
            'data': {
                'statistics': stats,
                'type': stats_type,
                'year': year,
                'month': month
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to retrieve statistics: {str(e)}'
            }
        }), 500

@users_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """Deactivate user account"""
    try:
        current_user = request.current_user
        
        # Prevent self-deactivation
        if current_user.id == user_id:
            return jsonify({
                'error': {
                    'code': 'SELF_DEACTIVATION',
                    'message': 'You cannot deactivate your own account'
                }
            }), 400
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        if not user.is_active:
            return jsonify({
                'error': {
                    'code': 'ALREADY_DEACTIVATED',
                    'message': 'User is already deactivated'
                }
            }), 400
        
        success = user.deactivate()
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'DEACTIVATION_FAILED',
                    'message': 'Failed to deactivate user'
                }
            }), 500
        
        return jsonify({
            'message': 'User deactivated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DEACTIVATION_ERROR',
                'message': f'Failed to deactivate user: {str(e)}'
            }
        }), 500

@users_bp.route('/search', methods=['GET'])
@admin_required
def search_users():
    """Search users"""
    try:
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not search_term:
            return jsonify({
                'error': {
                    'code': 'MISSING_SEARCH_TERM',
                    'message': 'Search term is required'
                }
            }), 400
        
        # Simple search implementation
        # In a production system, you might want to use full-text search
        from src.database import db_manager, Paginator
        
        query = """
        SELECT * FROM users 
        WHERE is_active = TRUE 
        AND (
            full_name ILIKE %s OR 
            username ILIKE %s OR 
            email ILIKE %s OR 
            current_assignment ILIKE %s OR
            diocese ILIKE %s OR
            province ILIKE %s
        )
        ORDER BY full_name
        """
        
        search_pattern = f"%{search_term}%"
        params = [search_pattern] * 6
        
        paginator = Paginator(page, per_page)
        result = paginator.paginate_query(query, tuple(params))
        
        # Convert users to dict
        users_data = [User(**user).to_dict() for user in result['items']]
        
        return jsonify({
            'message': 'Search completed successfully',
            'data': users_data,
            'pagination': result['pagination'],
            'search_term': search_term
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SEARCH_ERROR',
                'message': f'Search failed: {str(e)}'
            }
        }), 500

