"""
Mass Celebrations routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from src.auth import login_required
from src.models.mass_celebration import MassCelebration
from src.models.mass_intention import MassIntention
from src.models.bulk_intention import BulkIntention

mass_celebrations_bp = Blueprint('mass_celebrations', __name__)

@mass_celebrations_bp.route('', methods=['GET'])
@login_required
def get_mass_celebrations():
    """Get mass celebrations for current user"""
    try:
        current_user = request.current_user
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_START_DATE',
                        'message': 'Invalid start date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_END_DATE',
                        'message': 'Invalid end date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        # Get celebrations
        result = MassCelebration.find_by_priest(
            priest_id=current_user.id,
            start_date=start_date_obj,
            end_date=end_date_obj,
            page=page,
            per_page=per_page
        )
        
        # Convert to dict format
        celebrations_data = [MassCelebration(**celebration).to_dict() for celebration in result['items']]
        
        return jsonify({
            'message': 'Mass celebrations retrieved successfully',
            'data': celebrations_data,
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CELEBRATIONS_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve mass celebrations: {str(e)}'
            }
        }), 500

@mass_celebrations_bp.route('/<int:celebration_id>', methods=['GET'])
@login_required
def get_mass_celebration(celebration_id):
    """Get specific mass celebration"""
    try:
        current_user = request.current_user
        
        celebration = MassCelebration.find_by_id(celebration_id)
        if not celebration:
            return jsonify({
                'error': {
                    'code': 'CELEBRATION_NOT_FOUND',
                    'message': 'Mass celebration not found'
                }
            }), 404
        
        # Check if user owns this celebration
        if celebration.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view your own mass celebrations'
                }
            }), 403
        
        # Get additional details
        celebration_data = celebration.to_dict()
        
        # Add intention details if available
        if celebration.intention_id:
            intention_details = celebration.get_intention_details()
            celebration_data['intention_details'] = intention_details
        
        # Add bulk intention details if available
        if celebration.bulk_intention_id:
            bulk_details = celebration.get_bulk_intention_details()
            celebration_data['bulk_intention_details'] = bulk_details
        
        return jsonify({
            'message': 'Mass celebration retrieved successfully',
            'data': celebration_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CELEBRATION_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve mass celebration: {str(e)}'
            }
        }), 500

@mass_celebrations_bp.route('', methods=['POST'])
@login_required
def create_mass_celebration():
    """Create new mass celebration"""
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
        celebration_date_str = data.get('celebration_date')
        if not celebration_date_str:
            return jsonify({
                'error': {
                    'code': 'MISSING_CELEBRATION_DATE',
                    'message': 'Celebration date is required'
                }
            }), 400
        
        # Parse celebration date
        try:
            celebration_date = datetime.strptime(celebration_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_DATE_FORMAT',
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }
            }), 400
        
        # Optional fields
        intention_id = data.get('intention_id')
        bulk_intention_id = data.get('bulk_intention_id')
        mass_time_str = data.get('mass_time')
        location = data.get('location')
        notes = data.get('notes')
        attendees_count = data.get('attendees_count')
        special_circumstances = data.get('special_circumstances')
        
        # Parse mass time if provided
        mass_time = None
        if mass_time_str:
            try:
                mass_time = datetime.strptime(mass_time_str, '%H:%M').time()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_TIME_FORMAT',
                        'message': 'Invalid time format. Use HH:MM'
                    }
                }), 400
        
        # Validate that only one of intention_id or bulk_intention_id is provided
        if intention_id and bulk_intention_id:
            return jsonify({
                'error': {
                    'code': 'CONFLICTING_INTENTIONS',
                    'message': 'Cannot specify both intention_id and bulk_intention_id'
                }
            }), 400
        
        celebration = None
        message = ""
        
        if bulk_intention_id:
            # Create bulk mass celebration
            celebration, message = MassCelebration.create_with_bulk_intention(
                priest_id=current_user.id,
                celebration_date=celebration_date,
                bulk_intention_id=bulk_intention_id,
                mass_time=mass_time,
                location=location,
                notes=notes,
                attendees_count=attendees_count,
                special_circumstances=special_circumstances
            )
        elif intention_id:
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
                        'message': 'You can only celebrate masses for intentions assigned to you'
                    }
                }), 403
            
            # Check if intention can be celebrated on this date
            can_celebrate, reason = intention.can_be_celebrated_on(celebration_date)
            if not can_celebrate:
                return jsonify({
                    'error': {
                        'code': 'CANNOT_CELEBRATE',
                        'message': reason
                    }
                }), 400
            
            # Check if it's a personal mass
            if intention.intention_type == 'personal':
                celebration, message = MassCelebration.create_personal_mass(
                    priest_id=current_user.id,
                    celebration_date=celebration_date,
                    intention_id=intention_id,
                    mass_time=mass_time,
                    location=location,
                    notes=notes,
                    attendees_count=attendees_count,
                    special_circumstances=special_circumstances
                )
            else:
                # Regular intention mass
                celebration = MassCelebration.create(
                    priest_id=current_user.id,
                    celebration_date=celebration_date,
                    intention_id=intention_id,
                    mass_time=mass_time,
                    location=location,
                    notes=notes,
                    attendees_count=attendees_count,
                    special_circumstances=special_circumstances
                )
                message = "Mass celebration created successfully"
        else:
            # General mass without specific intention
            celebration = MassCelebration.create(
                priest_id=current_user.id,
                celebration_date=celebration_date,
                mass_time=mass_time,
                location=location,
                notes=notes,
                attendees_count=attendees_count,
                special_circumstances=special_circumstances
            )
            message = "Mass celebration created successfully"
        
        if not celebration:
            return jsonify({
                'error': {
                    'code': 'CREATION_FAILED',
                    'message': message or 'Failed to create mass celebration'
                }
            }), 500
        
        return jsonify({
            'message': message,
            'data': celebration.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CELEBRATION_CREATION_ERROR',
                'message': f'Failed to create mass celebration: {str(e)}'
            }
        }), 500

@mass_celebrations_bp.route('/<int:celebration_id>', methods=['PUT'])
@login_required
def update_mass_celebration(celebration_id):
    """Update mass celebration"""
    try:
        current_user = request.current_user
        
        celebration = MassCelebration.find_by_id(celebration_id)
        if not celebration:
            return jsonify({
                'error': {
                    'code': 'CELEBRATION_NOT_FOUND',
                    'message': 'Mass celebration not found'
                }
            }), 404
        
        # Check if user owns this celebration
        if celebration.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only update your own mass celebrations'
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
        
        # Fields that can be updated
        updatable_fields = ['celebration_date', 'mass_time', 'location', 'notes', 'attendees_count', 'special_circumstances']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                value = data[field]
                
                if field == 'celebration_date' and value:
                    try:
                        update_data[field] = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({
                            'error': {
                                'code': 'INVALID_DATE_FORMAT',
                                'message': 'Invalid date format. Use YYYY-MM-DD'
                            }
                        }), 400
                elif field == 'mass_time' and value:
                    try:
                        update_data[field] = datetime.strptime(value, '%H:%M').time()
                    except ValueError:
                        return jsonify({
                            'error': {
                                'code': 'INVALID_TIME_FORMAT',
                                'message': 'Invalid time format. Use HH:MM'
                            }
                        }), 400
                else:
                    update_data[field] = value
        
        if not update_data:
            return jsonify({
                'error': {
                    'code': 'NO_UPDATE_DATA',
                    'message': 'No valid fields to update'
                }
            }), 400
        
        # Update celebration
        success = celebration.update(**update_data)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'UPDATE_FAILED',
                    'message': 'Failed to update mass celebration'
                }
            }), 500
        
        return jsonify({
            'message': 'Mass celebration updated successfully',
            'data': celebration.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CELEBRATION_UPDATE_ERROR',
                'message': f'Failed to update mass celebration: {str(e)}'
            }
        }), 500

@mass_celebrations_bp.route('/<int:celebration_id>', methods=['DELETE'])
@login_required
def delete_mass_celebration(celebration_id):
    """Delete mass celebration"""
    try:
        current_user = request.current_user
        
        celebration = MassCelebration.find_by_id(celebration_id)
        if not celebration:
            return jsonify({
                'error': {
                    'code': 'CELEBRATION_NOT_FOUND',
                    'message': 'Mass celebration not found'
                }
            }), 404
        
        # Check if user owns this celebration
        if celebration.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only delete your own mass celebrations'
                }
            }), 403
        
        # Warning: Deleting a bulk mass celebration will affect the bulk intention count
        # This should be handled carefully in a production system
        
        success = celebration.delete()
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'DELETION_FAILED',
                    'message': 'Failed to delete mass celebration'
                }
            }), 500
        
        return jsonify({
            'message': 'Mass celebration deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CELEBRATION_DELETION_ERROR',
                'message': f'Failed to delete mass celebration: {str(e)}'
            }
        }), 500

@mass_celebrations_bp.route('/today', methods=['GET'])
@login_required
def get_today_celebrations():
    """Get today's mass celebrations"""
    try:
        current_user = request.current_user
        
        celebrations = MassCelebration.get_today_celebrations(current_user.id)
        celebrations_data = [celebration.to_dict() for celebration in celebrations]
        
        return jsonify({
            'message': "Today's mass celebrations retrieved successfully",
            'data': celebrations_data,
            'count': len(celebrations_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'TODAY_CELEBRATIONS_ERROR',
                'message': f"Failed to retrieve today's celebrations: {str(e)}"
            }
        }), 500

@mass_celebrations_bp.route('/monthly-summary', methods=['GET'])
@login_required
def get_monthly_summary():
    """Get monthly summary of mass celebrations"""
    try:
        current_user = request.current_user
        
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # Validate month
        if not (1 <= month <= 12):
            return jsonify({
                'error': {
                    'code': 'INVALID_MONTH',
                    'message': 'Month must be between 1 and 12'
                }
            }), 400
        
        summary = MassCelebration.get_monthly_summary(current_user.id, year, month)
        
        return jsonify({
            'message': 'Monthly summary retrieved successfully',
            'data': {
                'summary': summary,
                'year': year,
                'month': month
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'MONTHLY_SUMMARY_ERROR',
                'message': f'Failed to retrieve monthly summary: {str(e)}'
            }
        }), 500

@mass_celebrations_bp.route('/search', methods=['GET'])
@login_required
def search_mass_celebrations():
    """Search mass celebrations"""
    try:
        current_user = request.current_user
        
        # Query parameters
        search_term = request.args.get('q', '').strip()
        intention_type = request.args.get('intention_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Parse dates
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_START_DATE',
                        'message': 'Invalid start date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_END_DATE',
                        'message': 'Invalid end date format. Use YYYY-MM-DD'
                    }
                }), 400
        
        # Search celebrations
        result = MassCelebration.search(
            priest_id=current_user.id,
            search_term=search_term if search_term else None,
            intention_type=intention_type,
            start_date=start_date_obj,
            end_date=end_date_obj,
            page=page,
            per_page=per_page
        )
        
        # Convert to dict format
        celebrations_data = [MassCelebration(**celebration).to_dict() for celebration in result['items']]
        
        return jsonify({
            'message': 'Search completed successfully',
            'data': celebrations_data,
            'pagination': result['pagination'],
            'search_params': {
                'search_term': search_term,
                'intention_type': intention_type,
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SEARCH_ERROR',
                'message': f'Search failed: {str(e)}'
            }
        }), 500

