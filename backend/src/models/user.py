"""
User model for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import bcrypt
from src.database import db_manager, QueryBuilder

class User:
    """User model representing priests in the system"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.full_name = kwargs.get('full_name')
        self.ordination_date = kwargs.get('ordination_date')
        self.current_assignment = kwargs.get('current_assignment')
        self.diocese = kwargs.get('diocese')
        self.province = kwargs.get('province')
        self.phone = kwargs.get('phone')
        self.address = kwargs.get('address')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.last_login = kwargs.get('last_login')
        self.is_active = kwargs.get('is_active', True)
        self.profile_image_url = kwargs.get('profile_image_url')
        self.preferences = kwargs.get('preferences', {})
    
    @classmethod
    def create(cls, username: str, email: str, password: str, full_name: str, **kwargs) -> 'User':
        """Create a new user"""
        password_hash = cls.hash_password(password)
        
        data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'ordination_date': kwargs.get('ordination_date'),
            'current_assignment': kwargs.get('current_assignment'),
            'diocese': kwargs.get('diocese'),
            'province': kwargs.get('province'),
            'phone': kwargs.get('phone'),
            'address': kwargs.get('address'),
            'profile_image_url': kwargs.get('profile_image_url'),
            'preferences': kwargs.get('preferences', {})
        }
        
        query, params = QueryBuilder.build_insert('users', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def find_by_id(cls, user_id: int) -> Optional['User']:
        """Find user by ID"""
        query, params = QueryBuilder.build_select('users', where_conditions={'id': user_id, 'is_active': True})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional['User']:
        """Find user by username"""
        query, params = QueryBuilder.build_select('users', where_conditions={'username': username, 'is_active': True})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """Find user by email"""
        query, params = QueryBuilder.build_select('users', where_conditions={'email': email, 'is_active': True})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def get_all(cls, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get all active users with pagination"""
        from src.database import Paginator
        
        paginator = Paginator(page, per_page)
        base_query = "SELECT * FROM users WHERE is_active = TRUE ORDER BY full_name"
        count_query = "SELECT COUNT(*) as count FROM users WHERE is_active = TRUE"
        
        return paginator.paginate_query(base_query, count_query=count_query)
    
    def update(self, **kwargs) -> bool:
        """Update user information"""
        # Remove fields that shouldn't be updated directly
        update_data = {k: v for k, v in kwargs.items() 
                      if k not in ['id', 'uuid', 'created_at', 'password_hash']}
        
        if not update_data:
            return False
        
        update_data['updated_at'] = datetime.utcnow()
        
        query, params = QueryBuilder.build_update('users', update_data, {'id': self.id})
        affected_rows = db_manager.execute_update(query, params)
        
        if affected_rows > 0:
            # Update instance attributes
            for key, value in update_data.items():
                setattr(self, key, value)
            return True
        return False
    
    def update_password(self, new_password: str) -> bool:
        """Update user password"""
        password_hash = self.hash_password(new_password)
        
        query = "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (password_hash, datetime.utcnow(), self.id))
        
        if affected_rows > 0:
            self.password_hash = password_hash
            return True
        return False
    
    def update_last_login(self) -> bool:
        """Update last login timestamp"""
        now = datetime.utcnow()
        query = "UPDATE users SET last_login = %s WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (now, self.id))
        
        if affected_rows > 0:
            self.last_login = now
            return True
        return False
    
    def deactivate(self) -> bool:
        """Deactivate user account"""
        query = "UPDATE users SET is_active = FALSE, updated_at = %s WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (datetime.utcnow(), self.id))
        
        if affected_rows > 0:
            self.is_active = False
            return True
        return False
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not self.password_hash or not password:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for the user"""
        # Get today's mass status
        today_query = """
        SELECT COUNT(*) as count 
        FROM mass_celebrations 
        WHERE priest_id = %s AND celebration_date = CURRENT_DATE
        """
        today_masses = db_manager.execute_single(today_query, (self.id,))
        
        # Get current month personal mass progress
        month_query = """
        SELECT completed_count, target_count 
        FROM monthly_obligations 
        WHERE priest_id = %s 
        AND year = EXTRACT(YEAR FROM CURRENT_DATE) 
        AND month = EXTRACT(MONTH FROM CURRENT_DATE)
        """
        month_progress = db_manager.execute_single(month_query, (self.id,))
        
        # Get active bulk intentions
        bulk_query = """
        SELECT bi.*, mi.title as intention_title
        FROM bulk_intentions bi
        JOIN mass_intentions mi ON bi.intention_id = mi.id
        WHERE bi.priest_id = %s AND bi.current_count > 0
        ORDER BY bi.created_at
        """
        bulk_intentions = db_manager.execute_query(bulk_query, (self.id,))
        
        # Get unread notifications
        notifications_query = """
        SELECT COUNT(*) as count 
        FROM notifications 
        WHERE priest_id = %s AND is_read = FALSE
        """
        unread_notifications = db_manager.execute_single(notifications_query, (self.id,))
        
        return {
            'today_masses_count': today_masses['count'] if today_masses else 0,
            'monthly_progress': {
                'completed': month_progress['completed_count'] if month_progress else 0,
                'target': month_progress['target_count'] if month_progress else 3,
                'percentage': round((month_progress['completed_count'] / month_progress['target_count']) * 100, 1) if month_progress and month_progress['target_count'] > 0 else 0
            },
            'active_bulk_intentions': bulk_intentions or [],
            'unread_notifications_count': unread_notifications['count'] if unread_notifications else 0
        }
    
    def get_monthly_statistics(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """Get monthly mass statistics"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        # Get monthly celebrations
        celebrations_query = """
        SELECT 
            COUNT(*) as total_masses,
            COUNT(CASE WHEN mi.intention_type = 'personal' THEN 1 END) as personal_masses,
            COUNT(CASE WHEN bi.id IS NOT NULL THEN 1 END) as bulk_masses,
            COUNT(CASE WHEN mi.intention_type = 'fixed_date' THEN 1 END) as fixed_date_masses,
            COUNT(CASE WHEN mi.intention_type = 'special' THEN 1 END) as special_masses
        FROM mass_celebrations mc
        LEFT JOIN mass_intentions mi ON mc.intention_id = mi.id
        LEFT JOIN bulk_intentions bi ON mc.bulk_intention_id = bi.id
        WHERE mc.priest_id = %s 
        AND EXTRACT(YEAR FROM mc.celebration_date) = %s
        AND EXTRACT(MONTH FROM mc.celebration_date) = %s
        """
        stats = db_manager.execute_single(celebrations_query, (self.id, year, month))
        
        return stats or {
            'total_masses': 0,
            'personal_masses': 0,
            'bulk_masses': 0,
            'fixed_date_masses': 0,
            'special_masses': 0
        }
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'ordination_date': self.ordination_date.isoformat() if self.ordination_date else None,
            'current_assignment': self.current_assignment,
            'diocese': self.diocese,
            'province': self.province,
            'phone': self.phone,
            'address': self.address,
            'profile_image_url': self.profile_image_url,
            'preferences': self.preferences,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}: {self.full_name}>'

