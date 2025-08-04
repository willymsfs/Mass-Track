"""
Monthly Obligation model for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from src.database import db_manager, QueryBuilder

class MonthlyObligation:
    """Model representing monthly personal mass obligations"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.priest_id = kwargs.get('priest_id')
        self.year = kwargs.get('year')
        self.month = kwargs.get('month')
        self.completed_count = kwargs.get('completed_count', 0)
        self.target_count = kwargs.get('target_count', 3)
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
    
    @classmethod
    def get_or_create(cls, priest_id: int, year: int, month: int, target_count: int = 3) -> 'MonthlyObligation':
        """Get existing monthly obligation or create new one"""
        
        # Try to find existing
        existing = cls.find_by_priest_month(priest_id, year, month)
        if existing:
            return existing
        
        # Create new
        data = {
            'priest_id': priest_id,
            'year': year,
            'month': month,
            'completed_count': 0,
            'target_count': target_count
        }
        
        query, params = QueryBuilder.build_insert('monthly_obligations', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def find_by_id(cls, obligation_id: int) -> Optional['MonthlyObligation']:
        """Find monthly obligation by ID"""
        query, params = QueryBuilder.build_select('monthly_obligations', 
                                                 where_conditions={'id': obligation_id})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_priest_month(cls, priest_id: int, year: int, month: int) -> Optional['MonthlyObligation']:
        """Find monthly obligation for specific priest and month"""
        query, params = QueryBuilder.build_select('monthly_obligations', 
                                                 where_conditions={
                                                     'priest_id': priest_id,
                                                     'year': year,
                                                     'month': month
                                                 })
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_current_month(cls, priest_id: int) -> Optional['MonthlyObligation']:
        """Find current month's obligation for priest"""
        now = datetime.now()
        return cls.find_by_priest_month(priest_id, now.year, now.month)
    
    @classmethod
    def find_by_priest(cls, priest_id: int, year: int = None, 
                      page: int = 1, per_page: int = 12) -> Dict[str, Any]:
        """Find monthly obligations for a priest"""
        from src.database import Paginator
        
        where_conditions = {'priest_id': priest_id}
        if year:
            where_conditions['year'] = year
        
        paginator = Paginator(page, per_page)
        base_query, params = QueryBuilder.build_select('monthly_obligations', 
                                                      where_conditions=where_conditions,
                                                      order_by='year DESC, month DESC')
        
        return paginator.paginate_query(base_query, params)
    
    @classmethod
    def get_incomplete_obligations(cls, priest_id: int = None, 
                                  months_back: int = 6) -> List['MonthlyObligation']:
        """Get incomplete monthly obligations"""
        query = """
        SELECT mo.*, u.full_name as priest_name
        FROM monthly_obligations mo
        LEFT JOIN users u ON mo.priest_id = u.id
        WHERE mo.completed_count < mo.target_count
        AND (mo.year * 12 + mo.month) >= (EXTRACT(YEAR FROM CURRENT_DATE) * 12 + EXTRACT(MONTH FROM CURRENT_DATE) - %s)
        """
        params = [months_back]
        
        if priest_id:
            query += " AND mo.priest_id = %s"
            params.append(priest_id)
        
        query += " ORDER BY mo.year DESC, mo.month DESC"
        
        results = db_manager.execute_query(query, tuple(params))
        return [cls(**result) for result in results]
    
    @classmethod
    def get_yearly_summary(cls, priest_id: int, year: int) -> Dict[str, Any]:
        """Get yearly summary of monthly obligations"""
        query = """
        SELECT 
            COUNT(*) as total_months,
            SUM(completed_count) as total_completed,
            SUM(target_count) as total_target,
            COUNT(CASE WHEN completed_count >= target_count THEN 1 END) as completed_months,
            AVG(completed_count::DECIMAL / target_count) * 100 as avg_completion_percentage
        FROM monthly_obligations
        WHERE priest_id = %s AND year = %s
        """
        
        result = db_manager.execute_single(query, (priest_id, year))
        return result or {}
    
    def add_personal_mass(self, mass_celebration_id: int) -> tuple[bool, str]:
        """Add a personal mass to this monthly obligation"""
        
        if self.completed_count >= self.target_count:
            return False, "Monthly personal mass limit already reached"
        
        try:
            # Check if this mass is already linked
            existing_query = """
            SELECT id FROM personal_mass_celebrations 
            WHERE monthly_obligation_id = %s AND mass_celebration_id = %s
            """
            existing = db_manager.execute_single(existing_query, (self.id, mass_celebration_id))
            
            if existing:
                return False, "This mass is already counted towards monthly obligation"
            
            # Link the mass celebration
            link_query = """
            INSERT INTO personal_mass_celebrations (monthly_obligation_id, mass_celebration_id)
            VALUES (%s, %s)
            """
            db_manager.execute_update(link_query, (self.id, mass_celebration_id))
            
            # Update completed count
            update_query = """
            UPDATE monthly_obligations 
            SET completed_count = completed_count + 1, updated_at = %s
            WHERE id = %s
            """
            db_manager.execute_update(update_query, (datetime.utcnow(), self.id))
            
            # Update local instance
            self.completed_count += 1
            
            return True, f"Personal mass added. Progress: {self.completed_count}/{self.target_count}"
            
        except Exception as e:
            return False, f"Error adding personal mass: {str(e)}"
    
    def remove_personal_mass(self, mass_celebration_id: int) -> tuple[bool, str]:
        """Remove a personal mass from this monthly obligation"""
        
        try:
            # Check if this mass is linked
            existing_query = """
            SELECT id FROM personal_mass_celebrations 
            WHERE monthly_obligation_id = %s AND mass_celebration_id = %s
            """
            existing = db_manager.execute_single(existing_query, (self.id, mass_celebration_id))
            
            if not existing:
                return False, "This mass is not linked to this monthly obligation"
            
            # Remove the link
            unlink_query = """
            DELETE FROM personal_mass_celebrations 
            WHERE monthly_obligation_id = %s AND mass_celebration_id = %s
            """
            affected = db_manager.execute_update(unlink_query, (self.id, mass_celebration_id))
            
            if affected > 0:
                # Update completed count
                update_query = """
                UPDATE monthly_obligations 
                SET completed_count = GREATEST(0, completed_count - 1), updated_at = %s
                WHERE id = %s
                """
                db_manager.execute_update(update_query, (datetime.utcnow(), self.id))
                
                # Update local instance
                self.completed_count = max(0, self.completed_count - 1)
                
                return True, f"Personal mass removed. Progress: {self.completed_count}/{self.target_count}"
            
            return False, "Failed to remove personal mass link"
            
        except Exception as e:
            return False, f"Error removing personal mass: {str(e)}"
    
    def get_linked_masses(self) -> List[Dict[str, Any]]:
        """Get all mass celebrations linked to this monthly obligation"""
        query = """
        SELECT mc.*, pmc.created_at as linked_at
        FROM personal_mass_celebrations pmc
        JOIN mass_celebrations mc ON pmc.mass_celebration_id = mc.id
        WHERE pmc.monthly_obligation_id = %s
        ORDER BY mc.celebration_date DESC
        """
        
        return db_manager.execute_query(query, (self.id,))
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        if self.target_count == 0:
            return 100.0
        return round((self.completed_count / self.target_count) * 100, 1)
    
    def is_completed(self) -> bool:
        """Check if monthly obligation is completed"""
        return self.completed_count >= self.target_count
    
    def is_current_month(self) -> bool:
        """Check if this is the current month's obligation"""
        now = datetime.now()
        return self.year == now.year and self.month == now.month
    
    def is_overdue(self) -> bool:
        """Check if this obligation is overdue (past month and incomplete)"""
        if self.is_completed():
            return False
        
        now = datetime.now()
        obligation_month = self.year * 12 + self.month
        current_month = now.year * 12 + now.month
        
        return obligation_month < current_month
    
    def get_status(self) -> str:
        """Get status of monthly obligation"""
        if self.is_completed():
            return 'completed'
        elif self.is_overdue():
            return 'overdue'
        elif self.is_current_month():
            if self.completed_count >= (self.target_count * 0.67):
                return 'on_track'
            else:
                # Check if we're in the last week of the month
                now = datetime.now()
                if now.day > 24:  # Last week of month
                    return 'urgent'
                else:
                    return 'behind'
        else:
            return 'future'
    
    def get_remaining_count(self) -> int:
        """Get remaining masses needed"""
        return max(0, self.target_count - self.completed_count)
    
    def get_month_name(self) -> str:
        """Get month name"""
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return month_names[self.month - 1] if 1 <= self.month <= 12 else 'Unknown'
    
    def update_target_count(self, new_target: int) -> bool:
        """Update target count for this monthly obligation"""
        if new_target <= 0:
            return False
        
        query = "UPDATE monthly_obligations SET target_count = %s, updated_at = %s WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (new_target, datetime.utcnow(), self.id))
        
        if affected_rows > 0:
            self.target_count = new_target
            return True
        return False
    
    def recalculate_completed_count(self) -> bool:
        """Recalculate completed count based on linked masses"""
        query = """
        SELECT COUNT(*) as count 
        FROM personal_mass_celebrations 
        WHERE monthly_obligation_id = %s
        """
        result = db_manager.execute_single(query, (self.id,))
        actual_count = result['count'] if result else 0
        
        if actual_count != self.completed_count:
            update_query = """
            UPDATE monthly_obligations 
            SET completed_count = %s, updated_at = %s 
            WHERE id = %s
            """
            affected_rows = db_manager.execute_update(update_query, 
                                                    (actual_count, datetime.utcnow(), self.id))
            
            if affected_rows > 0:
                self.completed_count = actual_count
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert monthly obligation to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'priest_id': self.priest_id,
            'year': self.year,
            'month': self.month,
            'month_name': self.get_month_name(),
            'completed_count': self.completed_count,
            'target_count': self.target_count,
            'remaining_count': self.get_remaining_count(),
            'completion_percentage': self.get_completion_percentage(),
            'is_completed': self.is_completed(),
            'is_current_month': self.is_current_month(),
            'is_overdue': self.is_overdue(),
            'status': self.get_status(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MonthlyObligation {self.year}-{self.month:02d}: {self.completed_count}/{self.target_count}>'

