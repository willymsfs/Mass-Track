"""
Bulk Intention model for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from src.database import db_manager, QueryBuilder

class BulkIntention:
    """Model representing bulk mass intentions with pause/resume functionality"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.intention_id = kwargs.get('intention_id')
        self.priest_id = kwargs.get('priest_id')
        self.total_count = kwargs.get('total_count')
        self.current_count = kwargs.get('current_count')
        self.completed_count = kwargs.get('completed_count', 0)
        self.start_date = kwargs.get('start_date')
        self.estimated_end_date = kwargs.get('estimated_end_date')
        self.actual_end_date = kwargs.get('actual_end_date')
        self.is_paused = kwargs.get('is_paused', False)
        self.pause_reason = kwargs.get('pause_reason')
        self.paused_at = kwargs.get('paused_at')
        self.paused_count = kwargs.get('paused_count')
        self.resume_count = kwargs.get('resume_count')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.notes = kwargs.get('notes')
    
    @classmethod
    def create(cls, intention_id: int, priest_id: int, total_count: int, 
               start_date: date = None, **kwargs) -> 'BulkIntention':
        """Create a new bulk intention"""
        
        if total_count <= 0:
            raise ValueError("Total count must be greater than 0")
        
        if not start_date:
            start_date = date.today()
        
        # Calculate estimated end date (assuming 1 mass per day)
        from datetime import timedelta
        estimated_end_date = start_date + timedelta(days=total_count - 1)
        
        data = {
            'intention_id': intention_id,
            'priest_id': priest_id,
            'total_count': total_count,
            'current_count': total_count,
            'completed_count': 0,
            'start_date': start_date,
            'estimated_end_date': estimated_end_date,
            'notes': kwargs.get('notes')
        }
        
        query, params = QueryBuilder.build_insert('bulk_intentions', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def find_by_id(cls, bulk_id: int) -> Optional['BulkIntention']:
        """Find bulk intention by ID"""
        query, params = QueryBuilder.build_select('bulk_intentions', 
                                                 where_conditions={'id': bulk_id})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_active_by_priest(cls, priest_id: int) -> List['BulkIntention']:
        """Find active bulk intentions for a priest"""
        query = """
        SELECT bi.*, mi.title as intention_title, mi.description as intention_description
        FROM bulk_intentions bi
        JOIN mass_intentions mi ON bi.intention_id = mi.id
        WHERE bi.priest_id = %s AND bi.current_count > 0
        ORDER BY bi.created_at
        """
        
        results = db_manager.execute_query(query, (priest_id,))
        bulk_intentions = []
        
        for result in results:
            # Separate bulk intention data from intention data
            bulk_data = {k: v for k, v in result.items() 
                        if not k.startswith('intention_')}
            bulk_intention = cls(**bulk_data)
            
            # Add intention info as attributes
            bulk_intention.intention_title = result.get('intention_title')
            bulk_intention.intention_description = result.get('intention_description')
            
            bulk_intentions.append(bulk_intention)
        
        return bulk_intentions
    
    @classmethod
    def find_paused_by_priest(cls, priest_id: int) -> List['BulkIntention']:
        """Find paused bulk intentions for a priest"""
        query = """
        SELECT bi.*, mi.title as intention_title
        FROM bulk_intentions bi
        JOIN mass_intentions mi ON bi.intention_id = mi.id
        WHERE bi.priest_id = %s AND bi.is_paused = TRUE AND bi.current_count > 0
        ORDER BY bi.paused_at DESC
        """
        
        results = db_manager.execute_query(query, (priest_id,))
        return [cls(**result) for result in results]
    
    @classmethod
    def get_low_count_intentions(cls, priest_id: int = None, threshold: int = 10) -> List['BulkIntention']:
        """Get bulk intentions with low remaining count"""
        query = """
        SELECT bi.*, mi.title as intention_title, u.full_name as priest_name
        FROM bulk_intentions bi
        JOIN mass_intentions mi ON bi.intention_id = mi.id
        JOIN users u ON bi.priest_id = u.id
        WHERE bi.current_count > 0 AND bi.current_count <= %s
        """
        params = [threshold]
        
        if priest_id:
            query += " AND bi.priest_id = %s"
            params.append(priest_id)
        
        query += " ORDER BY bi.current_count, bi.created_at"
        
        results = db_manager.execute_query(query, tuple(params))
        return [cls(**result) for result in results]
    
    def celebrate_mass(self, celebration_date: date = None) -> tuple[bool, str, int]:
        """
        Celebrate one mass from this bulk intention
        Returns: (success, message, new_serial_number)
        """
        if not celebration_date:
            celebration_date = date.today()
        
        if self.is_paused:
            return False, "Cannot celebrate mass from paused bulk intention", self.current_count
        
        if self.current_count <= 0:
            return False, "Bulk intention is already completed", 0
        
        try:
            # Use the database function to update bulk intention count
            result = db_manager.call_function('update_bulk_intention_count', 
                                            (self.id, celebration_date))
            
            if result:
                # Update local instance
                self.current_count -= 1
                self.completed_count += 1
                
                if self.current_count == 0:
                    self.actual_end_date = celebration_date
                
                return True, "Mass celebrated successfully", self.current_count
            else:
                return False, "Failed to update bulk intention", self.current_count
                
        except Exception as e:
            return False, f"Error celebrating mass: {str(e)}", self.current_count
    
    def pause(self, reason: str) -> tuple[bool, str]:
        """Pause the bulk intention"""
        if self.is_paused:
            return False, "Bulk intention is already paused"
        
        if self.current_count <= 0:
            return False, "Cannot pause completed bulk intention"
        
        try:
            # Use the database function to pause bulk intention
            result = db_manager.call_function('pause_bulk_intention', (self.id, reason))
            
            if result:
                # Update local instance
                self.is_paused = True
                self.pause_reason = reason
                self.paused_at = datetime.utcnow()
                self.paused_count = self.current_count
                
                return True, "Bulk intention paused successfully"
            else:
                return False, "Failed to pause bulk intention"
                
        except Exception as e:
            return False, f"Error pausing bulk intention: {str(e)}"
    
    def resume(self) -> tuple[bool, str]:
        """Resume the paused bulk intention"""
        if not self.is_paused:
            return False, "Bulk intention is not paused"
        
        if self.current_count <= 0:
            return False, "Cannot resume completed bulk intention"
        
        try:
            # Use the database function to resume bulk intention
            result = db_manager.call_function('resume_bulk_intention', (self.id,))
            
            if result:
                # Update local instance
                self.is_paused = False
                self.pause_reason = None
                self.paused_at = None
                self.resume_count = self.current_count
                
                return True, "Bulk intention resumed successfully"
            else:
                return False, "Failed to resume bulk intention"
                
        except Exception as e:
            return False, f"Error resuming bulk intention: {str(e)}"
    
    def get_pause_history(self) -> List[Dict[str, Any]]:
        """Get pause/resume history for this bulk intention"""
        query = """
        SELECT * FROM pause_events 
        WHERE bulk_intention_id = %s 
        ORDER BY event_date DESC, created_at DESC
        """
        
        return db_manager.execute_query(query, (self.id,))
    
    def get_celebrations(self) -> List[Dict[str, Any]]:
        """Get all celebrations for this bulk intention"""
        query = """
        SELECT mc.*, u.full_name as priest_name
        FROM mass_celebrations mc
        JOIN users u ON mc.priest_id = u.id
        WHERE mc.bulk_intention_id = %s
        ORDER BY mc.serial_number DESC, mc.celebration_date DESC
        """
        
        return db_manager.execute_query(query, (self.id,))
    
    def get_progress_percentage(self) -> float:
        """Get completion percentage"""
        if self.total_count == 0:
            return 0.0
        return round((self.completed_count / self.total_count) * 100, 2)
    
    def get_estimated_completion_date(self, masses_per_day: float = 1.0) -> Optional[date]:
        """Estimate completion date based on current progress and rate"""
        if self.current_count <= 0:
            return self.actual_end_date
        
        if self.is_paused:
            return None
        
        from datetime import timedelta
        days_remaining = self.current_count / masses_per_day
        return date.today() + timedelta(days=int(days_remaining))
    
    def get_status_level(self, warning_threshold: int = 10, critical_threshold: int = 5) -> str:
        """Get status level based on remaining count"""
        if self.current_count <= 0:
            return 'completed'
        elif self.is_paused:
            return 'paused'
        elif self.current_count <= critical_threshold:
            return 'critical'
        elif self.current_count <= warning_threshold:
            return 'warning'
        else:
            return 'normal'
    
    def is_completed(self) -> bool:
        """Check if bulk intention is completed"""
        return self.current_count <= 0
    
    def can_celebrate_mass(self) -> tuple[bool, str]:
        """Check if a mass can be celebrated from this bulk intention"""
        if self.is_completed():
            return False, "Bulk intention is already completed"
        
        if self.is_paused:
            return False, "Bulk intention is currently paused"
        
        return True, "Mass can be celebrated"
    
    def update(self, **kwargs) -> bool:
        """Update bulk intention (limited fields)"""
        # Only allow updating certain fields
        allowed_fields = ['notes', 'estimated_end_date']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_data:
            return False
        
        update_data['updated_at'] = datetime.utcnow()
        
        query, params = QueryBuilder.build_update('bulk_intentions', update_data, {'id': self.id})
        affected_rows = db_manager.execute_update(query, params)
        
        if affected_rows > 0:
            # Update instance attributes
            for key, value in update_data.items():
                setattr(self, key, value)
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bulk intention to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'intention_id': self.intention_id,
            'priest_id': self.priest_id,
            'total_count': self.total_count,
            'current_count': self.current_count,
            'completed_count': self.completed_count,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'estimated_end_date': self.estimated_end_date.isoformat() if self.estimated_end_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'is_paused': self.is_paused,
            'pause_reason': self.pause_reason,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            'paused_count': self.paused_count,
            'resume_count': self.resume_count,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'progress_percentage': self.get_progress_percentage(),
            'status_level': self.get_status_level(),
            'is_completed': self.is_completed(),
            'estimated_completion_date': self.get_estimated_completion_date().isoformat() if self.get_estimated_completion_date() else None,
            # Include intention info if available
            'intention_title': getattr(self, 'intention_title', None),
            'intention_description': getattr(self, 'intention_description', None)
        }
    
    def __repr__(self):
        status = "paused" if self.is_paused else "active" if self.current_count > 0 else "completed"
        return f'<BulkIntention {self.id}: {self.current_count}/{self.total_count} ({status})>'

