"""
Excel Import routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
from src.auth import login_required
from src.models.excel_import import ExcelImportBatch, ExcelImportError, ExcelImportProcessor
from src.models.mass_celebration import MassCelebration
from src.models.notification import Notification

excel_import_bp = Blueprint('excel_import', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = current_app.config.get('ALLOWED_EXCEL_EXTENSIONS', ['xlsx', 'xls'])
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@excel_import_bp.route('/upload', methods=['POST'])
@login_required
def upload_excel_file():
    """Upload and validate Excel file"""
    try:
        current_user = request.current_user
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'error': {
                    'code': 'NO_FILE',
                    'message': 'No file provided'
                }
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': {
                    'code': 'NO_FILENAME',
                    'message': 'No file selected'
                }
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': {
                    'code': 'INVALID_FILE_TYPE',
                    'message': f'Invalid file type. Allowed types: {", ".join(current_app.config.get("ALLOWED_EXCEL_EXTENSIONS", ["xlsx", "xls"]))}'
                }
            }), 400
        
        # Check file size
        max_size = current_app.config.get('MAX_EXCEL_FILE_SIZE', 10485760)  # 10MB
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_size:
            return jsonify({
                'error': {
                    'code': 'FILE_TOO_LARGE',
                    'message': f'File size exceeds maximum allowed size of {max_size // 1048576}MB'
                }
            }), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{current_user.id}_{timestamp}_{filename}"
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Validate Excel file
        is_valid, message, file_info = ExcelImportProcessor.validate_excel_file(
            file_path, 
            max_rows=current_app.config.get('MAX_EXCEL_ROWS', 10000)
        )
        
        if not is_valid:
            # Remove invalid file
            os.remove(file_path)
            return jsonify({
                'error': {
                    'code': 'INVALID_EXCEL_FILE',
                    'message': message
                }
            }), 400
        
        # Detect date range
        year_start, year_end = ExcelImportProcessor.detect_date_range(file_path)
        
        # Create import batch
        import_batch = ExcelImportBatch.create(
            priest_id=current_user.id,
            filename=unique_filename,
            total_records=file_info['total_rows'],
            year_range_start=year_start,
            year_range_end=year_end
        )
        
        if not import_batch:
            os.remove(file_path)
            return jsonify({
                'error': {
                    'code': 'BATCH_CREATION_FAILED',
                    'message': 'Failed to create import batch'
                }
            }), 500
        
        return jsonify({
            'message': 'File uploaded and validated successfully',
            'data': {
                'batch_id': import_batch.uuid,
                'file_info': file_info,
                'year_range': {
                    'start': year_start,
                    'end': year_end
                },
                'file_path': file_path  # For processing
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'UPLOAD_ERROR',
                'message': f'File upload failed: {str(e)}'
            }
        }), 500

@excel_import_bp.route('/process/<batch_uuid>', methods=['POST'])
@login_required
def process_excel_import(batch_uuid):
    """Process uploaded Excel file"""
    try:
        current_user = request.current_user
        
        # Find import batch
        import_batch = ExcelImportBatch.find_by_uuid(batch_uuid)
        if not import_batch:
            return jsonify({
                'error': {
                    'code': 'BATCH_NOT_FOUND',
                    'message': 'Import batch not found'
                }
            }), 404
        
        # Check if user owns this batch
        if import_batch.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only process your own import batches'
                }
            }), 403
        
        # Check if already processed
        if import_batch.is_completed():
            return jsonify({
                'error': {
                    'code': 'ALREADY_PROCESSED',
                    'message': 'Import batch has already been processed'
                }
            }), 400
        
        data = request.get_json() or {}
        template_id = data.get('template_id', 1)  # Default template
        
        # Get file path
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        file_path = os.path.join(upload_folder, import_batch.filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Excel file not found'
                }
            }), 404
        
        # Process Excel data
        try:
            excel_data = ExcelImportProcessor.process_excel_data(file_path, template_id)
        except Exception as e:
            import_batch.update_status('failed', str(e))
            return jsonify({
                'error': {
                    'code': 'PROCESSING_FAILED',
                    'message': f'Failed to process Excel data: {str(e)}'
                }
            }), 500
        
        # Import data
        successful_imports = 0
        failed_imports = 0
        
        for row_index, row_data in enumerate(excel_data, start=1):
            try:
                # Map Excel columns to mass celebration fields
                # This is a simplified mapping - in production, you'd want more sophisticated mapping
                celebration_data = map_excel_row_to_celebration(row_data, current_user.id)
                
                if celebration_data:
                    # Create mass celebration
                    celebration = MassCelebration.create(
                        **celebration_data,
                        imported_from_excel=True,
                        import_batch_id=import_batch.uuid
                    )
                    
                    if celebration:
                        successful_imports += 1
                    else:
                        failed_imports += 1
                        ExcelImportError.create(
                            import_batch_id=batch_uuid,
                            row_number=row_index,
                            error_type='business_rule',
                            error_message='Failed to create mass celebration'
                        )
                else:
                    failed_imports += 1
                    ExcelImportError.create(
                        import_batch_id=batch_uuid,
                        row_number=row_index,
                        error_type='validation',
                        error_message='Invalid or missing required data'
                    )
                    
            except Exception as e:
                failed_imports += 1
                ExcelImportError.create(
                    import_batch_id=batch_uuid,
                    row_number=row_index,
                    error_type='format',
                    error_message=str(e)
                )
        
        # Update import batch progress
        import_batch.update_progress(successful_imports, failed_imports)
        
        # Create notification
        if successful_imports > 0:
            Notification.create_import_success(
                priest_id=current_user.id,
                batch_id=batch_uuid,
                successful_count=successful_imports,
                total_count=len(excel_data)
            )
        
        if failed_imports > 0:
            Notification.create_import_error(
                priest_id=current_user.id,
                batch_id=batch_uuid,
                error_message=f'{failed_imports} records failed to import'
            )
        
        # Clean up file
        try:
            os.remove(file_path)
        except:
            pass  # Don't fail if file cleanup fails
        
        return jsonify({
            'message': 'Excel import processing completed',
            'data': {
                'batch_id': batch_uuid,
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'total_records': len(excel_data),
                'success_rate': import_batch.get_success_rate()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'PROCESSING_ERROR',
                'message': f'Import processing failed: {str(e)}'
            }
        }), 500

def map_excel_row_to_celebration(row_data, priest_id):
    """Map Excel row data to mass celebration fields"""
    try:
        # This is a simplified mapping - adjust based on your Excel template
        # Expected columns: A=Date, B=Time, C=Location, D=Notes, E=Attendees
        
        celebration_date_str = row_data.get('A')  # Column A
        if not celebration_date_str:
            return None
        
        # Parse date
        try:
            if isinstance(celebration_date_str, str):
                celebration_date = datetime.strptime(celebration_date_str, '%Y-%m-%d').date()
            else:
                # Assume it's already a date object
                celebration_date = celebration_date_str
        except:
            return None
        
        # Parse time
        mass_time = None
        mass_time_str = row_data.get('B')  # Column B
        if mass_time_str:
            try:
                if isinstance(mass_time_str, str):
                    mass_time = datetime.strptime(mass_time_str, '%H:%M').time()
                else:
                    mass_time = mass_time_str
            except:
                pass
        
        # Other fields
        location = row_data.get('C')  # Column C
        notes = row_data.get('D')  # Column D
        attendees_count = None
        
        attendees_str = row_data.get('E')  # Column E
        if attendees_str:
            try:
                attendees_count = int(float(str(attendees_str)))
            except:
                pass
        
        return {
            'priest_id': priest_id,
            'celebration_date': celebration_date,
            'mass_time': mass_time,
            'location': location,
            'notes': notes,
            'attendees_count': attendees_count
        }
        
    except Exception:
        return None

@excel_import_bp.route('/batches', methods=['GET'])
@login_required
def get_import_batches():
    """Get import batches for current user"""
    try:
        current_user = request.current_user
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        result = ExcelImportBatch.find_by_priest(
            priest_id=current_user.id,
            page=page,
            per_page=per_page
        )
        
        # Convert to dict format
        batches_data = [ExcelImportBatch(**batch).to_dict() for batch in result['items']]
        
        return jsonify({
            'message': 'Import batches retrieved successfully',
            'data': batches_data,
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BATCHES_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve import batches: {str(e)}'
            }
        }), 500

@excel_import_bp.route('/batches/<batch_uuid>', methods=['GET'])
@login_required
def get_import_batch(batch_uuid):
    """Get specific import batch"""
    try:
        current_user = request.current_user
        
        import_batch = ExcelImportBatch.find_by_uuid(batch_uuid)
        if not import_batch:
            return jsonify({
                'error': {
                    'code': 'BATCH_NOT_FOUND',
                    'message': 'Import batch not found'
                }
            }), 404
        
        # Check if user owns this batch
        if import_batch.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view your own import batches'
                }
            }), 403
        
        # Get additional details
        batch_data = import_batch.to_dict()
        
        # Add error summary
        batch_data['error_summary'] = import_batch.get_error_summary()
        
        # Add recent errors
        errors = import_batch.get_errors()
        batch_data['recent_errors'] = [error.to_dict() for error in errors[:10]]
        batch_data['total_errors'] = len(errors)
        
        return jsonify({
            'message': 'Import batch retrieved successfully',
            'data': batch_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BATCH_RETRIEVAL_ERROR',
                'message': f'Failed to retrieve import batch: {str(e)}'
            }
        }), 500

@excel_import_bp.route('/batches/<batch_uuid>/errors', methods=['GET'])
@login_required
def get_import_batch_errors(batch_uuid):
    """Get errors for import batch"""
    try:
        current_user = request.current_user
        
        import_batch = ExcelImportBatch.find_by_uuid(batch_uuid)
        if not import_batch:
            return jsonify({
                'error': {
                    'code': 'BATCH_NOT_FOUND',
                    'message': 'Import batch not found'
                }
            }), 404
        
        # Check if user owns this batch
        if import_batch.priest_id != current_user.id:
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You can only view errors from your own import batches'
                }
            }), 403
        
        error_type = request.args.get('error_type')
        errors = ExcelImportError.find_by_batch(batch_uuid, error_type)
        errors_data = [error.to_dict() for error in errors]
        
        return jsonify({
            'message': 'Import batch errors retrieved successfully',
            'data': errors_data,
            'count': len(errors_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BATCH_ERRORS_ERROR',
                'message': f'Failed to retrieve import batch errors: {str(e)}'
            }
        }), 500

@excel_import_bp.route('/templates', methods=['GET'])
@login_required
def get_import_templates():
    """Get available import templates"""
    try:
        # Return predefined templates
        templates = [
            {
                'id': 1,
                'name': 'Standard Template',
                'description': 'Standard mass tracking template with date, time, location, notes, and attendees',
                'columns': {
                    'A': 'Date (YYYY-MM-DD)',
                    'B': 'Time (HH:MM)',
                    'C': 'Location',
                    'D': 'Notes',
                    'E': 'Attendees Count'
                }
            },
            {
                'id': 2,
                'name': 'Detailed Template',
                'description': 'Detailed template with additional fields for intention type and special circumstances',
                'columns': {
                    'A': 'Date (YYYY-MM-DD)',
                    'B': 'Time (HH:MM)',
                    'C': 'Location',
                    'D': 'Intention Type',
                    'E': 'Notes',
                    'F': 'Attendees Count',
                    'G': 'Special Circumstances'
                }
            },
            {
                'id': 3,
                'name': 'Simple Template',
                'description': 'Simple template with just date and basic information',
                'columns': {
                    'A': 'Date (YYYY-MM-DD)',
                    'B': 'Location',
                    'C': 'Notes'
                }
            }
        ]
        
        return jsonify({
            'message': 'Import templates retrieved successfully',
            'data': templates
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'TEMPLATES_ERROR',
                'message': f'Failed to retrieve import templates: {str(e)}'
            }
        }), 500

@excel_import_bp.route('/statistics', methods=['GET'])
@login_required
def get_import_statistics():
    """Get import statistics for current user"""
    try:
        current_user = request.current_user
        
        year_start = request.args.get('year_start', type=int)
        year_end = request.args.get('year_end', type=int)
        
        statistics = ExcelImportProcessor.get_import_statistics(
            priest_id=current_user.id,
            year_start=year_start,
            year_end=year_end
        )
        
        return jsonify({
            'message': 'Import statistics retrieved successfully',
            'data': statistics
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to retrieve import statistics: {str(e)}'
            }
        }), 500

