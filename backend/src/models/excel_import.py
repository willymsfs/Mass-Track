"""
Excel Import models for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
import uuid as uuid_lib
from src.database import db_manager, QueryBuilder

class ExcelImportBatch:
    """Model representing Excel import batches"""
    
    STATUSES = ['processing', 'completed', 'failed', 'partial']
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.priest_id = kwargs.get('priest_id')
        self.filename = kwargs.get('filename')
        self.import_date = kwargs.get('import_date')
        self.total_records = kwargs.get('total_records')
        self.successful_imports = kwargs.get('successful_imports', 0)
        self.failed_imports = kwargs.get('failed_imports', 0)
        self.year_range_start = kwargs.get('year_range_start')
        self.year_range_end = kwargs.get('year_range_end')
        self.status = kwargs.get('status', 'processing')
        self.error_log = kwargs.get('error_log')
        self.created_at = kwargs.get('created_at')
    
    @classmethod
    def create(cls, priest_id: int, filename: str, total_records: int, 
               year_range_start: int = None, year_range_end: int = None) -> 'ExcelImportBatch':
        """Create a new Excel import batch"""
        
        batch_uuid = str(uuid_lib.uuid4())
        
        data = {
            'uuid': batch_uuid,
            'priest_id': priest_id,
            'filename': filename,
            'total_records': total_records,
            'year_range_start': year_range_start,
            'year_range_end': year_range_end,
            'status': 'processing'
        }
        
        query, params = QueryBuilder.build_insert('excel_import_batches', data, 'id, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def find_by_id(cls, batch_id: int) -> Optional['ExcelImportBatch']:
        """Find import batch by ID"""
        query, params = QueryBuilder.build_select('excel_import_batches', 
                                                 where_conditions={'id': batch_id})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_uuid(cls, batch_uuid: str) -> Optional['ExcelImportBatch']:
        """Find import batch by UUID"""
        query, params = QueryBuilder.build_select('excel_import_batches', 
                                                 where_conditions={'uuid': batch_uuid})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_priest(cls, priest_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Find import batches for a priest"""
        from src.database import Paginator
        
        paginator = Paginator(page, per_page)
        base_query, params = QueryBuilder.build_select('excel_import_batches', 
                                                      where_conditions={'priest_id': priest_id},
                                                      order_by='import_date DESC')
        
        return paginator.paginate_query(base_query, params)
    
    @classmethod
    def get_recent_imports(cls, priest_id: int = None, days: int = 7) -> List['ExcelImportBatch']:
        """Get recent import batches"""
        query = """
        SELECT eib.*, u.full_name as priest_name
        FROM excel_import_batches eib
        LEFT JOIN users u ON eib.priest_id = u.id
        WHERE eib.import_date >= NOW() - INTERVAL '%s days'
        """
        params = [days]
        
        if priest_id:
            query += " AND eib.priest_id = %s"
            params.append(priest_id)
        
        query += " ORDER BY eib.import_date DESC"
        
        results = db_manager.execute_query(query, tuple(params))
        return [cls(**result) for result in results]
    
    def update_status(self, status: str, error_log: str = None) -> bool:
        """Update import batch status"""
        if status not in self.STATUSES:
            raise ValueError(f"Invalid status: {status}")
        
        update_data = {'status': status}
        if error_log:
            update_data['error_log'] = error_log
        
        query, params = QueryBuilder.build_update('excel_import_batches', update_data, {'id': self.id})
        affected_rows = db_manager.execute_update(query, params)
        
        if affected_rows > 0:
            self.status = status
            if error_log:
                self.error_log = error_log
            return True
        return False
    
    def update_progress(self, successful_imports: int, failed_imports: int) -> bool:
        """Update import progress"""
        update_data = {
            'successful_imports': successful_imports,
            'failed_imports': failed_imports
        }
        
        # Determine final status
        if failed_imports == 0:
            status = 'completed'
        elif successful_imports == 0:
            status = 'failed'
        else:
            status = 'partial'
        
        update_data['status'] = status
        
        query, params = QueryBuilder.build_update('excel_import_batches', update_data, {'id': self.id})
        affected_rows = db_manager.execute_update(query, params)
        
        if affected_rows > 0:
            self.successful_imports = successful_imports
            self.failed_imports = failed_imports
            self.status = status
            return True
        return False
    
    def get_errors(self) -> List['ExcelImportError']:
        """Get all errors for this import batch"""
        return ExcelImportError.find_by_batch(self.uuid)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of import errors"""
        query = """
        SELECT 
            error_type,
            COUNT(*) as count,
            array_agg(DISTINCT column_name) as affected_columns
        FROM excel_import_errors 
        WHERE import_batch_id = %s
        GROUP BY error_type
        ORDER BY count DESC
        """
        
        results = db_manager.execute_query(query, (self.uuid,))
        return results or []
    
    def get_success_rate(self) -> float:
        """Get import success rate percentage"""
        if self.total_records == 0:
            return 0.0
        return round((self.successful_imports / self.total_records) * 100, 2)
    
    def is_completed(self) -> bool:
        """Check if import is completed"""
        return self.status in ['completed', 'failed', 'partial']
    
    def delete(self) -> bool:
        """Delete import batch and related data"""
        # This will cascade delete related errors and celebrations
        query = "DELETE FROM excel_import_batches WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (self.id,))
        return affected_rows > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert import batch to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'priest_id': self.priest_id,
            'filename': self.filename,
            'import_date': self.import_date.isoformat() if self.import_date else None,
            'total_records': self.total_records,
            'successful_imports': self.successful_imports,
            'failed_imports': self.failed_imports,
            'year_range_start': self.year_range_start,
            'year_range_end': self.year_range_end,
            'status': self.status,
            'error_log': self.error_log,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'success_rate': self.get_success_rate(),
            'is_completed': self.is_completed()
        }
    
    def __repr__(self):
        return f'<ExcelImportBatch {self.id}: {self.filename} ({self.status})>'


class ExcelImportError:
    """Model representing Excel import errors"""
    
    ERROR_TYPES = ['validation', 'format', 'missing', 'duplicate', 'business_rule']
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.import_batch_id = kwargs.get('import_batch_id')
        self.row_number = kwargs.get('row_number')
        self.column_name = kwargs.get('column_name')
        self.error_type = kwargs.get('error_type')
        self.error_message = kwargs.get('error_message')
        self.raw_value = kwargs.get('raw_value')
        self.suggested_value = kwargs.get('suggested_value')
        self.created_at = kwargs.get('created_at')
    
    @classmethod
    def create(cls, import_batch_id: str, row_number: int, error_type: str, 
               error_message: str, **kwargs) -> 'ExcelImportError':
        """Create a new import error"""
        
        if error_type not in cls.ERROR_TYPES:
            raise ValueError(f"Invalid error type: {error_type}")
        
        data = {
            'import_batch_id': import_batch_id,
            'row_number': row_number,
            'column_name': kwargs.get('column_name'),
            'error_type': error_type,
            'error_message': error_message,
            'raw_value': kwargs.get('raw_value'),
            'suggested_value': kwargs.get('suggested_value')
        }
        
        query, params = QueryBuilder.build_insert('excel_import_errors', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def find_by_batch(cls, batch_uuid: str, error_type: str = None) -> List['ExcelImportError']:
        """Find errors for an import batch"""
        where_conditions = {'import_batch_id': batch_uuid}
        if error_type:
            where_conditions['error_type'] = error_type
        
        query, params = QueryBuilder.build_select('excel_import_errors', 
                                                 where_conditions=where_conditions,
                                                 order_by='row_number, created_at')
        results = db_manager.execute_query(query, params)
        return [cls(**result) for result in results]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert import error to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'import_batch_id': self.import_batch_id,
            'row_number': self.row_number,
            'column_name': self.column_name,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'raw_value': self.raw_value,
            'suggested_value': self.suggested_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ExcelImportError {self.id}: Row {self.row_number} ({self.error_type})>'


class ExcelImportProcessor:
    """Utility class for processing Excel imports"""
    
    @staticmethod
    def validate_excel_file(file_path: str, max_rows: int = 10000) -> tuple[bool, str, Dict[str, Any]]:
        """Validate Excel file and return basic info"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Basic validation
            if df.empty:
                return False, "Excel file is empty", {}
            
            if len(df) > max_rows:
                return False, f"Excel file has too many rows ({len(df)}). Maximum allowed: {max_rows}", {}
            
            # Get file info
            info = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': df.columns.tolist(),
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
            }
            
            return True, "Excel file is valid", info
            
        except Exception as e:
            return False, f"Error reading Excel file: {str(e)}", {}
    
    @staticmethod
    def detect_date_range(file_path: str, date_column: str = None) -> tuple[Optional[int], Optional[int]]:
        """Detect year range from Excel file"""
        try:
            df = pd.read_excel(file_path)
            
            # Try to find date column
            date_columns = []
            if date_column and date_column in df.columns:
                date_columns = [date_column]
            else:
                # Look for common date column names
                common_names = ['date', 'celebration_date', 'mass_date', 'Date', 'Celebration Date']
                date_columns = [col for col in df.columns if col in common_names]
            
            if not date_columns:
                # Try first column that might contain dates
                for col in df.columns:
                    if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower():
                        date_columns = [col]
                        break
            
            if not date_columns:
                return None, None
            
            # Extract years from date column
            date_col = date_columns[0]
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            valid_dates = df[date_col].dropna()
            
            if valid_dates.empty:
                return None, None
            
            min_year = valid_dates.dt.year.min()
            max_year = valid_dates.dt.year.max()
            
            return int(min_year), int(max_year)
            
        except Exception:
            return None, None
    
    @staticmethod
    def process_excel_data(file_path: str, template_id: int = None) -> List[Dict[str, Any]]:
        """Process Excel file and return structured data"""
        try:
            df = pd.read_excel(file_path)
            
            # Convert to list of dictionaries
            # Use column letters as keys (A, B, C, etc.)
            processed_data = []
            
            for index, row in df.iterrows():
                row_data = {}
                for col_index, value in enumerate(row):
                    col_letter = chr(65 + col_index)  # A, B, C, etc.
                    
                    # Handle different data types
                    if pd.isna(value):
                        row_data[col_letter] = None
                    elif isinstance(value, pd.Timestamp):
                        row_data[col_letter] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, (int, float)):
                        row_data[col_letter] = str(value)
                    else:
                        row_data[col_letter] = str(value).strip()
                
                processed_data.append(row_data)
            
            return processed_data
            
        except Exception as e:
            raise Exception(f"Error processing Excel data: {str(e)}")
    
    @staticmethod
    def get_import_statistics(priest_id: int, year_start: int = None, year_end: int = None) -> Dict[str, Any]:
        """Get import statistics for a priest"""
        try:
            result = db_manager.call_function('get_import_statistics', 
                                            (priest_id, year_start, year_end))
            return result or {}
        except Exception:
            return {}

