"""
Mass Intention model for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from src.database import db_manager, QueryBuilder

class MassIntention:
    """Model representing mass intentions"""
    
    INTENTION_TYPES = ['personal', 'bulk', 'fixed_date', 'special', 'anniversary', 'birthday', 'deceased']
    SOURCES = ['personal', 'province', 'generalate', 'parish', 'individual', 'family', 'organization']
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.intention_type = kwargs.get('intention_type')
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.source = kwargs.get('source')
        self.source_contact = kwargs.get('source_contact', {})
        self.created_by = kwargs.get('created_by')
        self.assigned_to = kwargs.get('assigned_to')
        self.priority = kwargs.get('priority', 1)
        self.is_fixed_date = kwargs.get('is_fixed_date', False)
        self.fixed_date = kwargs.get('fixed_date')
        self.deadline_date = kwargs.get('deadline_date')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.metadata = kwargs.get('metadata', {})
        self.is_active = kwargs.get('is_active', True)
    
    @classmethod
    def create(cls, intention_type: str, title: str, source: str, created_by: int, 
               assigned_to: int = None, **kwargs) -> 'MassIntention':
        """Create a new mass intention"""
        
        if intention_type not in cls.INTENTION_TYPES:
            raise ValueError(f"Invalid intention type: {intention_type}")
        
        if source not in cls.SOURCES:
            raise ValueError(f"Invalid source: {source}")
        
        data = {
            'intention_type': intention_type,
            'title': title,
            'description': kwargs.get('description'),
            'source': source,
            'source_contact': kwargs.get('source_contact', {}),
            'created_by': created_by,
            'assigned_to': assigned_to or created_by,
            'priority': kwargs.get('priority', 1),
            'is_fixed_date': kwargs.get('is_fixed_date', False),
            'fixed_date': kwargs.get('fixed_date'),
            'deadline_date': kwargs.get('deadline_date'),
            'metadata': kwargs.get('metadata', {})
        }
        
        query, params = QueryBuilder.build_insert('mass_intentions', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def find_by_id(cls, intention_id: int) -> Optional['MassIntention']:
        """Find mass intention by ID"""
        query, params = QueryBuilder.build_select('mass_intentions', 
                                                 where_conditions={'id': intention_id, 'is_active': True})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_priest(cls, priest_id: int, intention_type: str = None, 
                      page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Find mass intentions assigned to a priest"""
        from src.database import Paginator
        
        where_conditions = {'assigned_to': priest_id, 'is_active': True}
        if intention_type:
            where_conditions['intention_type'] = intention_type
        
        paginator = Paginator(page, per_page)
        base_query, params = QueryBuilder.build_select('mass_intentions', 
                                                      where_conditions=where_conditions,
                                                      order_by='created_at DESC')
        
        return paginator.paginate_query(base_query, params)
    
    @classmethod
    def get_fixed_date_intentions(cls, priest_id: int, start_date: date = None, 
                                 end_date: date = None) -> List['MassIntention']:
        """Get fixed date intentions for a priest within date range"""
        query = """
        SELECT * FROM mass_intentions 
        WHERE assigned_to = %s AND is_fixed_date = TRUE AND is_active = TRUE
        """
        params = [priest_id]
        
        if start_date:
            query += " AND fixed_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND fixed_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY fixed_date"
        
        results = db_manager.execute_query(query, tuple(params))
        return [cls(**result) for result in results]
    
    @classmethod
    def get_upcoming_fixed_dates(cls, priest_id: int, days_ahead: int = 30) -> List['MassIntention']:
        """Get upcoming fixed date intentions"""
        query = """
        SELECT * FROM mass_intentions 
        WHERE assigned_to = %s AND is_fixed_date = TRUE AND is_active = TRUE
        AND fixed_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
        ORDER BY fixed_date
        """
        
        results = db_manager.execute_query(query, (priest_id, days_ahead))
        return [cls(**result) for result in results]
    
    @classmethod
    def search(cls, priest_id: int = None, search_term: str = None, 
              intention_type: str = None, source: str = None,
              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Search mass intentions with filters"""
        from src.database import Paginator
        
        query = "SELECT * FROM mass_intentions WHERE is_active = TRUE"
        params = []
        
        if priest_id:
            query += " AND assigned_to = %s"
            params.append(priest_id)
        
        if search_term:
            query += " AND (title ILIKE %s OR description ILIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        if intention_type:
            query += " AND intention_type = %s"
            params.append(intention_type)
        
        if source:
            query += " AND source = %s"
            params.append(source)
        
        query += " ORDER BY created_at DESC"
        
        paginator = Paginator(page, per_page)
        return paginator.paginate_query(query, tuple(params))
    
    def update(self, **kwargs) -> bool:
        """Update mass intention"""
        # Remove fields that shouldn't be updated directly
        update_data = {k: v for k, v in kwargs.items() 
                      if k not in ['id', 'uuid', 'created_at', 'created_by']}
        
        if not update_data:
            return False
        
        update_data['updated_at'] = datetime.utcnow()
        
        query, params = QueryBuilder.build_update('mass_intentions', update_data, {'id': self.id})
        affected_rows = db_manager.execute_update(query, params)
        
        if affected_rows > 0:
            # Update instance attributes
            for key, value in update_data.items():
                setattr(self, key, value)
            return True
        return False
    
    def deactivate(self) -> bool:
        """Deactivate mass intention"""
        query = "UPDATE mass_intentions SET is_active = FALSE, updated_at = %s WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (datetime.utcnow(), self.id))
        
        if affected_rows > 0:
            self.is_active = False
            return True
        return False
    
    def get_celebrations(self) -> List[Dict[str, Any]]:
        """Get all celebrations for this intention"""
        query = """
        SELECT mc.*, u.full_name as priest_name
        FROM mass_celebrations mc
        JOIN users u ON mc.priest_id = u.id
        WHERE mc.intention_id = %s
        ORDER BY mc.celebration_date DESC
        """
        
        return db_manager.execute_query(query, (self.id,))
    
    def get_celebration_count(self) -> int:
        """Get count of celebrations for this intention"""
        query = "SELECT COUNT(*) as count FROM mass_celebrations WHERE intention_id = %s"
        result = db_manager.execute_single(query, (self.id,))
        return result['count'] if result else 0
    
    def is_completed(self) -> bool:
        """Check if intention is completed (has at least one celebration)"""
        return self.get_celebration_count() > 0
    
    def can_be_celebrated_on(self, celebration_date: date) -> tuple[bool, str]:
        """Check if intention can be celebrated on given date"""
        if not self.is_active:
            return False, "Intention is not active"
        
        if self.is_fixed_date and self.fixed_date:
            if celebration_date != self.fixed_date:
                return False, f"This intention must be celebrated on {self.fixed_date}"
        
        if self.deadline_date and celebration_date > self.deadline_date:
            return False, f"Celebration date is past the deadline ({self.deadline_date})"
        
        # Check if already celebrated (for non-bulk intentions)
        if self.intention_type != 'bulk' and self.is_completed():
            return False, "This intention has already been celebrated"
        
        return True, "Can be celebrated"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mass intention to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'intention_type': self.intention_type,
            'title': self.title,
            'description': self.description,
            'source': self.source,
            'source_contact': self.source_contact,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'priority': self.priority,
            'is_fixed_date': self.is_fixed_date,
            'fixed_date': self.fixed_date.isoformat() if self.fixed_date else None,
            'deadline_date': self.deadline_date.isoformat() if self.deadline_date else None,
            'metadata': self.metadata,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'celebration_count': self.get_celebration_count(),
            'is_completed': self.is_completed()
        }
    
    def __repr__(self):
        return f'<MassIntention {self.id}: {self.title} ({self.intention_type})>'

