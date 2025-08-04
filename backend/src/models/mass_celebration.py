"""
Mass Celebration model for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime, date, time
from typing import Optional, Dict, Any, List
from src.database import db_manager, QueryBuilder

class MassCelebration:
    """Model representing actual mass celebrations"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.priest_id = kwargs.get('priest_id')
        self.celebration_date = kwargs.get('celebration_date')
        self.intention_id = kwargs.get('intention_id')
        self.bulk_intention_id = kwargs.get('bulk_intention_id')
        self.serial_number = kwargs.get('serial_number')
        self.mass_time = kwargs.get('mass_time')
        self.location = kwargs.get('location')
        self.notes = kwargs.get('notes')
        self.attendees_count = kwargs.get('attendees_count')
        self.special_circumstances = kwargs.get('special_circumstances')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.imported_from_excel = kwargs.get('imported_from_excel', False)
        self.import_batch_id = kwargs.get('import_batch_id')
    
    @classmethod
    def create(cls, priest_id: int, celebration_date: date, **kwargs) -> 'MassCelebration':
        """Create a new mass celebration"""
        
        # Validate celebration date
        if celebration_date > date.today():
            raise ValueError("Mass celebration date cannot be in the future")
        
        data = {
            'priest_id': priest_id,
            'celebration_date': celebration_date,
            'intention_id': kwargs.get('intention_id'),
            'bulk_intention_id': kwargs.get('bulk_intention_id'),
            'serial_number': kwargs.get('serial_number'),
            'mass_time': kwargs.get('mass_time'),
            'location': kwargs.get('location'),
            'notes': kwargs.get('notes'),
            'attendees_count': kwargs.get('attendees_count'),
            'special_circumstances': kwargs.get('special_circumstances'),
            'imported_from_excel': kwargs.get('imported_from_excel', False),
            'import_batch_id': kwargs.get('import_batch_id')
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        query, params = QueryBuilder.build_insert('mass_celebrations', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def create_with_bulk_intention(cls, priest_id: int, celebration_date: date, 
                                  bulk_intention_id: int, **kwargs) -> tuple[Optional['MassCelebration'], str]:
        """Create mass celebration and update bulk intention count"""
        from src.models.bulk_intention import BulkIntention
        
        # Get bulk intention
        bulk_intention = BulkIntention.find_by_id(bulk_intention_id)
        if not bulk_intention:
            return None, "Bulk intention not found"
        
        # Check if bulk intention can be celebrated
        can_celebrate, message = bulk_intention.can_celebrate_mass()
        if not can_celebrate:
            return None, message
        
        # Create the celebration with serial number
        serial_number = bulk_intention.current_count
        
        celebration = cls.create(
            priest_id=priest_id,
            celebration_date=celebration_date,
            bulk_intention_id=bulk_intention_id,
            serial_number=serial_number,
            **kwargs
        )
        
        if celebration:
            # Update bulk intention count
            success, update_message, new_count = bulk_intention.celebrate_mass(celebration_date)
            if success:
                return celebration, f"Mass celebrated successfully. Remaining: {new_count}"
            else:
                # If bulk update failed, we should delete the celebration
                celebration.delete()
                return None, update_message
        
        return None, "Failed to create mass celebration"
    
    @classmethod
    def create_personal_mass(cls, priest_id: int, celebration_date: date, 
                           intention_id: int = None, **kwargs) -> tuple[Optional['MassCelebration'], str]:
        """Create personal mass celebration and update monthly obligations"""
        
        # Create the celebration
        celebration = cls.create(
            priest_id=priest_id,
            celebration_date=celebration_date,
            intention_id=intention_id,
            **kwargs
        )
        
        if celebration:
            # Update monthly obligation
            try:
                result = db_manager.call_function('update_monthly_obligation', 
                                                (priest_id, celebration_date, celebration.id))
                if result:
                    return celebration, "Personal mass recorded successfully"
                else:
                    return celebration, "Mass recorded but monthly obligation update failed"
            except Exception as e:
                # Mass was created but monthly obligation failed
                return celebration, f"Mass recorded but monthly obligation error: {str(e)}"
        
        return None, "Failed to create personal mass celebration"
    
    @classmethod
    def find_by_id(cls, celebration_id: int) -> Optional['MassCelebration']:
        """Find mass celebration by ID"""
        query, params = QueryBuilder.build_select('mass_celebrations', 
                                                 where_conditions={'id': celebration_id})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_priest(cls, priest_id: int, start_date: date = None, end_date: date = None,
                      page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Find mass celebrations for a priest with optional date range"""
        from src.database import Paginator
        
        query = """
        SELECT mc.*, 
               mi.title as intention_title, 
               mi.intention_type,
               bi.total_count as bulk_total,
               bi.current_count as bulk_remaining
        FROM mass_celebrations mc
        LEFT JOIN mass_intentions mi ON mc.intention_id = mi.id
        LEFT JOIN bulk_intentions bi ON mc.bulk_intention_id = bi.id
        WHERE mc.priest_id = %s
        """
        params = [priest_id]
        
        if start_date:
            query += " AND mc.celebration_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND mc.celebration_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY mc.celebration_date DESC, mc.created_at DESC"
        
        paginator = Paginator(page, per_page)
        return paginator.paginate_query(query, tuple(params))
    
    @classmethod
    def find_by_date(cls, celebration_date: date, priest_id: int = None) -> List['MassCelebration']:
        """Find mass celebrations on a specific date"""
        where_conditions = {'celebration_date': celebration_date}
        if priest_id:
            where_conditions['priest_id'] = priest_id
        
        query, params = QueryBuilder.build_select('mass_celebrations', 
                                                 where_conditions=where_conditions,
                                                 order_by='mass_time, created_at')
        results = db_manager.execute_query(query, params)
        return [cls(**result) for result in results]
    
    @classmethod
    def get_today_celebrations(cls, priest_id: int) -> List['MassCelebration']:
        """Get today's mass celebrations for a priest"""
        return cls.find_by_date(date.today(), priest_id)
    
    @classmethod
    def get_monthly_summary(cls, priest_id: int, year: int, month: int) -> Dict[str, Any]:
        """Get monthly summary of mass celebrations"""
        query = """
        SELECT 
            COUNT(*) as total_masses,
            COUNT(CASE WHEN mi.intention_type = 'personal' THEN 1 END) as personal_masses,
            COUNT(CASE WHEN mc.bulk_intention_id IS NOT NULL THEN 1 END) as bulk_masses,
            COUNT(CASE WHEN mi.intention_type = 'fixed_date' THEN 1 END) as fixed_date_masses,
            COUNT(CASE WHEN mi.intention_type = 'special' THEN 1 END) as special_masses,
            COUNT(CASE WHEN mi.intention_type = 'anniversary' THEN 1 END) as anniversary_masses,
            COUNT(CASE WHEN mi.intention_type = 'birthday' THEN 1 END) as birthday_masses,
            COUNT(CASE WHEN mi.intention_type = 'deceased' THEN 1 END) as deceased_masses,
            AVG(mc.attendees_count) as avg_attendees,
            MIN(mc.celebration_date) as first_mass_date,
            MAX(mc.celebration_date) as last_mass_date
        FROM mass_celebrations mc
        LEFT JOIN mass_intentions mi ON mc.intention_id = mi.id
        WHERE mc.priest_id = %s 
        AND EXTRACT(YEAR FROM mc.celebration_date) = %s
        AND EXTRACT(MONTH FROM mc.celebration_date) = %s
        """
        
        result = db_manager.execute_single(query, (priest_id, year, month))
        return result or {}
    
    @classmethod
    def get_yearly_summary(cls, priest_id: int, year: int) -> Dict[str, Any]:
        """Get yearly summary of mass celebrations"""
        query = """
        SELECT 
            COUNT(*) as total_masses,
            COUNT(DISTINCT EXTRACT(MONTH FROM celebration_date)) as active_months,
            COUNT(CASE WHEN mi.intention_type = 'personal' THEN 1 END) as personal_masses,
            COUNT(CASE WHEN mc.bulk_intention_id IS NOT NULL THEN 1 END) as bulk_masses,
            AVG(mc.attendees_count) as avg_attendees,
            SUM(mc.attendees_count) as total_attendees
        FROM mass_celebrations mc
        LEFT JOIN mass_intentions mi ON mc.intention_id = mi.id
        WHERE mc.priest_id = %s 
        AND EXTRACT(YEAR FROM mc.celebration_date) = %s
        """
        
        result = db_manager.execute_single(query, (priest_id, year))
        return result or {}
    
    @classmethod
    def search(cls, priest_id: int = None, search_term: str = None, 
              intention_type: str = None, start_date: date = None, end_date: date = None,
              page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Search mass celebrations with filters"""
        from src.database import Paginator
        
        query = """
        SELECT mc.*, 
               mi.title as intention_title, 
               mi.intention_type,
               u.full_name as priest_name
        FROM mass_celebrations mc
        LEFT JOIN mass_intentions mi ON mc.intention_id = mi.id
        LEFT JOIN users u ON mc.priest_id = u.id
        WHERE 1=1
        """
        params = []
        
        if priest_id:
            query += " AND mc.priest_id = %s"
            params.append(priest_id)
        
        if search_term:
            query += " AND (mi.title ILIKE %s OR mc.notes ILIKE %s OR mc.location ILIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if intention_type:
            query += " AND mi.intention_type = %s"
            params.append(intention_type)
        
        if start_date:
            query += " AND mc.celebration_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND mc.celebration_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY mc.celebration_date DESC, mc.created_at DESC"
        
        paginator = Paginator(page, per_page)
        return paginator.paginate_query(query, tuple(params))
    
    def update(self, **kwargs) -> bool:
        """Update mass celebration"""
        # Remove fields that shouldn't be updated directly
        update_data = {k: v for k, v in kwargs.items() 
                      if k not in ['id', 'uuid', 'created_at', 'priest_id', 'bulk_intention_id', 'serial_number']}
        
        if not update_data:
            return False
        
        # Validate celebration date if being updated
        if 'celebration_date' in update_data and update_data['celebration_date'] > date.today():
            raise ValueError("Mass celebration date cannot be in the future")
        
        update_data['updated_at'] = datetime.utcnow()
        
        query, params = QueryBuilder.build_update('mass_celebrations', update_data, {'id': self.id})
        affected_rows = db_manager.execute_update(query, params)
        
        if affected_rows > 0:
            # Update instance attributes
            for key, value in update_data.items():
                setattr(self, key, value)
            return True
        return False
    
    def delete(self) -> bool:
        """Delete mass celebration (use with caution - affects bulk intention counts)"""
        query = "DELETE FROM mass_celebrations WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (self.id,))
        return affected_rows > 0
    
    def get_intention_details(self) -> Optional[Dict[str, Any]]:
        """Get details of the associated mass intention"""
        if not self.intention_id:
            return None
        
        query = """
        SELECT mi.*, u.full_name as created_by_name
        FROM mass_intentions mi
        LEFT JOIN users u ON mi.created_by = u.id
        WHERE mi.id = %s
        """
        
        return db_manager.execute_single(query, (self.intention_id,))
    
    def get_bulk_intention_details(self) -> Optional[Dict[str, Any]]:
        """Get details of the associated bulk intention"""
        if not self.bulk_intention_id:
            return None
        
        query = """
        SELECT bi.*, mi.title as intention_title
        FROM bulk_intentions bi
        JOIN mass_intentions mi ON bi.intention_id = mi.id
        WHERE bi.id = %s
        """
        
        return db_manager.execute_single(query, (self.bulk_intention_id,))
    
    def is_personal_mass(self) -> bool:
        """Check if this is a personal mass celebration"""
        if self.intention_id:
            intention = self.get_intention_details()
            return intention and intention.get('intention_type') == 'personal'
        return False
    
    def is_bulk_mass(self) -> bool:
        """Check if this is a bulk mass celebration"""
        return self.bulk_intention_id is not None
    
    def get_celebration_type(self) -> str:
        """Get the type of mass celebration"""
        if self.is_bulk_mass():
            return 'bulk'
        elif self.intention_id:
            intention = self.get_intention_details()
            return intention.get('intention_type', 'unknown') if intention else 'unknown'
        else:
            return 'general'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mass celebration to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'priest_id': self.priest_id,
            'celebration_date': self.celebration_date.isoformat() if self.celebration_date else None,
            'intention_id': self.intention_id,
            'bulk_intention_id': self.bulk_intention_id,
            'serial_number': self.serial_number,
            'mass_time': self.mass_time.isoformat() if self.mass_time else None,
            'location': self.location,
            'notes': self.notes,
            'attendees_count': self.attendees_count,
            'special_circumstances': self.special_circumstances,
            'imported_from_excel': self.imported_from_excel,
            'import_batch_id': self.import_batch_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'celebration_type': self.get_celebration_type(),
            'is_personal_mass': self.is_personal_mass(),
            'is_bulk_mass': self.is_bulk_mass()
        }
    
    def __repr__(self):
        return f'<MassCelebration {self.id}: {self.celebration_date} ({self.get_celebration_type()})>'

