"""
Notification model for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from src.database import db_manager, QueryBuilder

class Notification:
    """Model representing system notifications and reminders"""
    
    NOTIFICATION_TYPES = ['reminder', 'warning', 'info', 'success', 'error']
    PRIORITIES = ['low', 'normal', 'high', 'urgent']
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.uuid = kwargs.get('uuid')
        self.priest_id = kwargs.get('priest_id')
        self.notification_type = kwargs.get('notification_type')
        self.title = kwargs.get('title')
        self.message = kwargs.get('message')
        self.is_read = kwargs.get('is_read', False)
        self.priority = kwargs.get('priority', 'normal')
        self.scheduled_for = kwargs.get('scheduled_for')
        self.created_at = kwargs.get('created_at')
        self.read_at = kwargs.get('read_at')
        self.related_entity_type = kwargs.get('related_entity_type')
        self.related_entity_id = kwargs.get('related_entity_id')
    
    @classmethod
    def create(cls, priest_id: int, notification_type: str, title: str, message: str, 
               priority: str = 'normal', **kwargs) -> 'Notification':
        """Create a new notification"""
        
        if notification_type not in cls.NOTIFICATION_TYPES:
            raise ValueError(f"Invalid notification type: {notification_type}")
        
        if priority not in cls.PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")
        
        data = {
            'priest_id': priest_id,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'priority': priority,
            'scheduled_for': kwargs.get('scheduled_for'),
            'related_entity_type': kwargs.get('related_entity_type'),
            'related_entity_id': kwargs.get('related_entity_id')
        }
        
        query, params = QueryBuilder.build_insert('notifications', data, 'id, uuid, created_at')
        result = db_manager.execute_insert_returning(query, params)
        
        if result:
            data.update(result)
            return cls(**data)
        return None
    
    @classmethod
    def create_bulk_intention_warning(cls, priest_id: int, bulk_intention_id: int, 
                                    remaining_count: int) -> 'Notification':
        """Create warning notification for low bulk intention count"""
        title = "Bulk Intention Low Count"
        message = f"Your bulk intention has only {remaining_count} masses remaining. Consider planning your celebration schedule."
        
        return cls.create(
            priest_id=priest_id,
            notification_type='warning',
            title=title,
            message=message,
            priority='high',
            related_entity_type='bulk_intentions',
            related_entity_id=bulk_intention_id
        )
    
    @classmethod
    def create_monthly_reminder(cls, priest_id: int, completed_count: int, 
                              target_count: int, month_name: str) -> 'Notification':
        """Create reminder for monthly personal masses"""
        remaining = target_count - completed_count
        title = "Monthly Personal Masses"
        message = f"You have completed {completed_count} out of {target_count} personal masses for {month_name}. Remember to complete the remaining {remaining} before month end."
        
        priority = 'urgent' if remaining > 0 and datetime.now().day > 24 else 'normal'
        
        return cls.create(
            priest_id=priest_id,
            notification_type='reminder',
            title=title,
            message=message,
            priority=priority,
            related_entity_type='monthly_obligations',
            related_entity_id=None
        )
    
    @classmethod
    def create_fixed_date_reminder(cls, priest_id: int, intention_id: int, 
                                 intention_title: str, fixed_date: str) -> 'Notification':
        """Create reminder for upcoming fixed date mass"""
        title = "Fixed Date Mass Approaching"
        message = f'"{intention_title}" is scheduled for {fixed_date}. Please prepare accordingly.'
        
        return cls.create(
            priest_id=priest_id,
            notification_type='reminder',
            title=title,
            message=message,
            priority='high',
            related_entity_type='mass_intentions',
            related_entity_id=intention_id
        )
    
    @classmethod
    def create_import_success(cls, priest_id: int, batch_id: str, 
                            successful_count: int, total_count: int) -> 'Notification':
        """Create notification for successful Excel import"""
        title = "Excel Import Completed"
        message = f"Successfully imported {successful_count} out of {total_count} mass records from your Excel file."
        
        return cls.create(
            priest_id=priest_id,
            notification_type='success',
            title=title,
            message=message,
            priority='normal',
            related_entity_type='excel_import_batches',
            related_entity_id=batch_id
        )
    
    @classmethod
    def create_import_error(cls, priest_id: int, batch_id: str, 
                          error_message: str) -> 'Notification':
        """Create notification for Excel import error"""
        title = "Excel Import Failed"
        message = f"There was an error importing your Excel file: {error_message}"
        
        return cls.create(
            priest_id=priest_id,
            notification_type='error',
            title=title,
            message=message,
            priority='high',
            related_entity_type='excel_import_batches',
            related_entity_id=batch_id
        )
    
    @classmethod
    def find_by_id(cls, notification_id: int) -> Optional['Notification']:
        """Find notification by ID"""
        query, params = QueryBuilder.build_select('notifications', 
                                                 where_conditions={'id': notification_id})
        result = db_manager.execute_single(query, params)
        return cls(**result) if result else None
    
    @classmethod
    def find_by_priest(cls, priest_id: int, is_read: bool = None, 
                      page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Find notifications for a priest"""
        from src.database import Paginator
        
        where_conditions = {'priest_id': priest_id}
        if is_read is not None:
            where_conditions['is_read'] = is_read
        
        paginator = Paginator(page, per_page)
        base_query, params = QueryBuilder.build_select('notifications', 
                                                      where_conditions=where_conditions,
                                                      order_by='created_at DESC')
        
        return paginator.paginate_query(base_query, params)
    
    @classmethod
    def get_unread_count(cls, priest_id: int) -> int:
        """Get count of unread notifications for a priest"""
        query = "SELECT COUNT(*) as count FROM notifications WHERE priest_id = %s AND is_read = FALSE"
        result = db_manager.execute_single(query, (priest_id,))
        return result['count'] if result else 0
    
    @classmethod
    def get_urgent_notifications(cls, priest_id: int) -> List['Notification']:
        """Get urgent unread notifications for a priest"""
        query = """
        SELECT * FROM notifications 
        WHERE priest_id = %s AND is_read = FALSE AND priority = 'urgent'
        ORDER BY created_at DESC
        """
        
        results = db_manager.execute_query(query, (priest_id,))
        return [cls(**result) for result in results]
    
    @classmethod
    def get_scheduled_notifications(cls, up_to_time: datetime = None) -> List['Notification']:
        """Get notifications scheduled for delivery"""
        if not up_to_time:
            up_to_time = datetime.utcnow()
        
        query = """
        SELECT * FROM notifications 
        WHERE scheduled_for IS NOT NULL 
        AND scheduled_for <= %s 
        AND is_read = FALSE
        ORDER BY scheduled_for
        """
        
        results = db_manager.execute_query(query, (up_to_time,))
        return [cls(**result) for result in results]
    
    @classmethod
    def mark_all_read(cls, priest_id: int) -> int:
        """Mark all notifications as read for a priest"""
        query = """
        UPDATE notifications 
        SET is_read = TRUE, read_at = %s 
        WHERE priest_id = %s AND is_read = FALSE
        """
        
        return db_manager.execute_update(query, (datetime.utcnow(), priest_id))
    
    @classmethod
    def delete_old_notifications(cls, days_old: int = 30) -> int:
        """Delete old read notifications"""
        query = """
        DELETE FROM notifications 
        WHERE is_read = TRUE 
        AND read_at < NOW() - INTERVAL '%s days'
        """
        
        return db_manager.execute_update(query, (days_old,))
    
    def mark_as_read(self) -> bool:
        """Mark notification as read"""
        if self.is_read:
            return True
        
        query = "UPDATE notifications SET is_read = TRUE, read_at = %s WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (datetime.utcnow(), self.id))
        
        if affected_rows > 0:
            self.is_read = True
            self.read_at = datetime.utcnow()
            return True
        return False
    
    def mark_as_unread(self) -> bool:
        """Mark notification as unread"""
        if not self.is_read:
            return True
        
        query = "UPDATE notifications SET is_read = FALSE, read_at = NULL WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (self.id,))
        
        if affected_rows > 0:
            self.is_read = False
            self.read_at = None
            return True
        return False
    
    def delete(self) -> bool:
        """Delete notification"""
        query = "DELETE FROM notifications WHERE id = %s"
        affected_rows = db_manager.execute_update(query, (self.id,))
        return affected_rows > 0
    
    def get_related_entity(self) -> Optional[Dict[str, Any]]:
        """Get the related entity details"""
        if not self.related_entity_type or not self.related_entity_id:
            return None
        
        table_map = {
            'mass_intentions': 'mass_intentions',
            'bulk_intentions': 'bulk_intentions',
            'mass_celebrations': 'mass_celebrations',
            'monthly_obligations': 'monthly_obligations',
            'excel_import_batches': 'excel_import_batches'
        }
        
        table = table_map.get(self.related_entity_type)
        if not table:
            return None
        
        query = f"SELECT * FROM {table} WHERE id = %s"
        return db_manager.execute_single(query, (self.related_entity_id,))
    
    def is_urgent(self) -> bool:
        """Check if notification is urgent"""
        return self.priority == 'urgent'
    
    def is_overdue(self) -> bool:
        """Check if scheduled notification is overdue"""
        if not self.scheduled_for:
            return False
        return self.scheduled_for < datetime.utcnow() and not self.is_read
    
    def get_age_in_hours(self) -> float:
        """Get notification age in hours"""
        if not self.created_at:
            return 0
        
        delta = datetime.utcnow() - self.created_at
        return delta.total_seconds() / 3600
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'priest_id': self.priest_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'priority': self.priority,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'related_entity_type': self.related_entity_type,
            'related_entity_id': self.related_entity_id,
            'is_urgent': self.is_urgent(),
            'is_overdue': self.is_overdue(),
            'age_in_hours': self.get_age_in_hours()
        }
    
    def __repr__(self):
        status = "read" if self.is_read else "unread"
        return f'<Notification {self.id}: {self.title} ({self.priority}, {status})>'

