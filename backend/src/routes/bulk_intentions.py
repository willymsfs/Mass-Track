"""
Bulk Intentions routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from src.auth import login_required
from src.models.bulk_intention import BulkIntention
from src.models.mass_intention import MassIntention

bulk_intentions_bp = Blueprint('bulk_intentions', __name__)

@bulk_intentions_bp.route('', methods=['GET'])
@login_required
def get_bulk_intentions():
    """Get bulk intentions for current user"""
    try:
        current_user = request.current_user
        
        # Query parameters
        status = request.args.get('status')  # 'active', 'paused', 'completed'
        
        if status == 'active':
            bulk_intentions = BulkIntention.find_active_by_priest(current_user.id)
        elif status == 'paused':
            bulk_intentions = BulkIntention.find_paused_by_priest(current_user.id)
        else:
            # Get all bulk intentions (you might want to add pagination here)
            bulk_intentions = BulkIntention.find_active_by_priest(current_user.id)
        
        bulk_intentions_data = [bulk_intention.to_dict() for bulk_intention in bulk_intentions]
        
        return jsonify({
            'message': 'Bulk intentions retrieved successfully',
            'data': bulk_intentions_data,
            'count': len(bulk_intentions_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_INTENTIONS_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve bulk intentions: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>', methods=['GET'])
@login_required
def get_bulk_intention(bulk_intention_id):
    """Get specific bulk intention"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view your own bulk intentions'
                }
            }), 403
        
        # Get additional details
        bulk_intention_data = bulk_intention.to_dict()
        
        # Add pause history
        bulk_intention_data['pause_history'] = bulk_intention.get_pause_history()
        
        # Add recent celebrations
        celebrations = bulk_intention.get_celebrations()
        bulk_intention_data['recent_celebrations'] = celebrations[:10]  # Last 10 celebrations
        bulk_intention_data['total_celebrations'] = len(celebrations)
        
        return jsonify({
            'message': 'Bulk intention retrieved successfully',
            'data': bulk_intention_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_INTENTION_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve bulk intention: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('', methods=['POST'])
@login_required
def create_bulk_intention():
    """Create new bulk intention"""
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
        intention_id = data.get('intention_id')
        total_count = data.get('total_count')
        
        if not intention_id:
            return jsonify({
                'error': {
                    'code': 'MISSING_INTENTION_ID',
                    'message': 'Intention ID is required'
                }
            }), 400
        
        if not total_count or total_count <= 0:
            return jsonify({
                'error': {
                    'code': 'INVALID_TOTAL_COUNT',
                    'message': 'Total count must be a positive integer'
                }
            }), 400
        
        # Validate intention exists and belongs to user
        intention = MassIntention.find_by_id(intention_id)
        if not intention:
            return jsonify({
                'error': {
                    'code': 'INTENTION_NOT_FOUND',
                    'message': 'Mass intention not found'
                }
            }), 404
        
        if intention.assigned_to != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only create bulk intentions for intentions assigned to you'
                }
            }), 403
        
        # Check if intention is suitable for bulk
        if intention.intention_type not in ['bulk', 'province', 'generalate']:
            return jsonify({
                'error': {
                    'code': 'INVALID_INTENTION_TYPE',
                    'message': 'This intention type is not suitable for bulk processing'
                }
            }), 400
        
        # Optional fields
        start_date_str = data.get('start_date')
        notes = data.get('notes')
        
        # Parse start date
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        # Create bulk intention
        bulk_intention = BulkIntention.create(
            intention_id=intention_id,
            priest_id=current_user.id,
            total_count=total_count,
            start_date=start_date,
            notes=notes
        )
        
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'CREATION_FAILED',
                    'message': 'Failed to create bulk intention'
                }
            }), 500
        
        return jsonify({
            'message': 'Bulk intention created successfully',
            'data': bulk_intention.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_INTENTION_CREATION_ERROR',
                'message': f'Failed to create bulk intention: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>/celebrate', methods=['POST'])
@login_required
def celebrate_bulk_mass(bulk_intention_id):
    """Celebrate one mass from bulk intention"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only celebrate masses from your own bulk intentions'
                }
            }), 403
        
        data = request.get_json() or {}
        
        # Optional celebration date (defaults to today)
        celebration_date_str = data.get('celebration_date')
        celebration_date = date.today()
        
        if celebration_date_str:
            try:
                celebration_date = datetime.strptime(celebration_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        # Celebrate mass
        success, message, new_serial_number = bulk_intention.celebrate_mass(celebration_date)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'CELEBRATION_FAILED',
                    'message': message
                }
            }), 400
        
        return jsonify({
            'message': message,
            'data': {
                'bulk_intention_id': bulk_intention_id,
                'new_serial_number': new_serial_number,
                'remaining_count': new_serial_number,
                'celebration_date': celebration_date.isoformat(),
                'is_completed': new_serial_number == 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_CELEBRATION_ERROR',
                'message': f'Failed to celebrate bulk mass: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>/pause', methods=['POST'])
@login_required
def pause_bulk_intention(bulk_intention_id):
    """Pause bulk intention"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only pause your own bulk intentions'
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
        
        reason = data.get('reason', '').strip()
        if not reason:
            return jsonify({
                'error': {
                    'code': 'MISSING_REASON',
                    'message': 'Pause reason is required'
                }
            }), 400
        
        # Pause bulk intention
        success, message = bulk_intention.pause(reason)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'PAUSE_FAILED',
                    'message': message
                }
            }), 400
        
        return jsonify({
            'message': message,
            'data': bulk_intention.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_PAUSE_ERROR',
                'message': f'Failed to pause bulk intention: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>/resume', methods=['POST'])
@login_required
def resume_bulk_intention(bulk_intention_id):
    """Resume paused bulk intention"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only resume your own bulk intentions'
                }
            }), 403
        
        # Resume bulk intention
        success, message = bulk_intention.resume()
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'RESUME_FAILED',
                    'message': message
                }
            }), 400
        
        return jsonify({
            'message': message,
            'data': bulk_intention.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_RESUME_ERROR',
                'message': f'Failed to resume bulk intention: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>/celebrations', methods=['GET'])
@login_required
def get_bulk_intention_celebrations(bulk_intention_id):
    """Get celebrations for bulk intention"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view celebrations from your own bulk intentions'
                }
            }), 403
        
        celebrations = bulk_intention.get_celebrations()
        
        return jsonify({
            'message': 'Bulk intention celebrations retrieved successfully',
            'data': celebrations,
            'count': len(celebrations)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_CELEBRATIONS_ERROR',
                'message': f'Failed to retrieve bulk intention celebrations: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>/pause-history', methods=['GET'])
@login_required
def get_bulk_intention_pause_history(bulk_intention_id):
    """Get pause/resume history for bulk intention"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view pause history from your own bulk intentions'
                }
            }), 403
        
        pause_history = bulk_intention.get_pause_history()
        
        return jsonify({
            'message': 'Bulk intention pause history retrieved successfully',
            'data': pause_history,
            'count': len(pause_history)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_PAUSE_HISTORY_ERROR',
                'message': f'Failed to retrieve bulk intention pause history: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/low-count', methods=['GET'])
@login_required
def get_low_count_bulk_intentions():
    """Get bulk intentions with low remaining count"""
    try:
        current_user = request.current_user
        
        threshold = request.args.get('threshold', 10, type=int)
        
        low_count_intentions = BulkIntention.get_low_count_intentions(
            priest_id=current_user.id,
            threshold=threshold
        )
        
        low_count_data = [intention.to_dict() for intention in low_count_intentions]
        
        return jsonify({
            'message': 'Low count bulk intentions retrieved successfully',
            'data': low_count_data,
            'count': len(low_count_data),
            'threshold': threshold
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOW_COUNT_ERROR',
                'message': f'Failed to retrieve low count bulk intentions: {str(e)}'
            }
        }), 500

@bulk_intentions_bp.route('/<int:bulk_intention_id>', methods=['PUT'])
@login_required
def update_bulk_intention(bulk_intention_id):
    """Update bulk intention (limited fields)"""
    try:
        current_user = request.current_user
        
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return jsonify({
                'error': {
                    'code': 'BULK_INTENTION_NOT_FOUND',
                    'message': 'Bulk intention not found'
                }
            }), 404
        
        # Check if user owns this bulk intention
        if bulk_intention.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only update your own bulk intentions'
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
        
        # Only allow updating certain fields
        update_data = {}
        
        if 'notes' in data:
            update_data['notes'] = data['notes']
        
        if 'estimated_end_date' in data:
            try:
                update_data['estimated_end_date'] = datetime.strptime(data['estimated_end_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        if not update_data:
            return jsonify({
                'error': {
                    'code': 'NO_UPDATE_DATA',
                    'message': 'No valid fields to update'
                }
            }), 400
        
        # Update bulk intention
        success = bulk_intention.update(**update_data)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update bulk intention'
                }
            }), 500
        
        return jsonify({
            'message': 'Bulk intention updated successfully',
            'data': bulk_intention.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_INTENTION_UPDATE_ERROR',
                'message': f'Failed to update bulk intention: {str(e)}'
            }
        }), 500

