"""
Database connection and utilities for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from flask import current_app, g
from contextlib import contextmanager
import logging
from typing import Optional, Dict, Any, List
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        self.pool: Optional[ThreadedConnectionPool] = None
        
    def init_app(self, app):
        """Initialize database with Flask app"""
        self.app = app
        
        # Create connection pool
        try:
            database_url = app.config.get('DATABASE_URL')
            if database_url:
                self.pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dsn=database_url
                )
                logger.info("Database connection pool created successfully")
            else:
                logger.error("DATABASE_URL not configured")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """Get database cursor with automatic connection management"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory or psycopg2.extras.RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database cursor error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a SELECT query and return single result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_insert_returning(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute an INSERT query with RETURNING clause"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def call_function(self, function_name: str, params: tuple = None) -> Any:
        """Call a PostgreSQL function"""
        with self.get_cursor() as cursor:
            cursor.callproc(function_name, params)
            return cursor.fetchone()
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

def init_database(app):
    """Initialize database with Flask app"""
    db_manager.init_app(app)
    
    # Create upload directory if it doesn't exist
    upload_dir = app.config.get('UPLOAD_FOLDER')
    if upload_dir and not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        logger.info(f"Created upload directory: {upload_dir}")

def get_db():
    """Get database manager instance"""
    return db_manager

# Database utility functions
def validate_database_connection():
    """Validate database connection and schema"""
    try:
        result = db_manager.execute_single("SELECT version()")
        logger.info(f"Database connection successful: {result['version']}")
        
        # Check if required tables exist
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'mass_intentions', 'mass_celebrations', 'bulk_intentions')
        """
        tables = db_manager.execute_query(tables_query)
        table_names = [table['table_name'] for table in tables]
        
        required_tables = ['users', 'mass_intentions', 'mass_celebrations', 'bulk_intentions']
        missing_tables = [table for table in required_tables if table not in table_names]
        
        if missing_tables:
            logger.warning(f"Missing required tables: {missing_tables}")
            return False
        
        logger.info("All required tables exist")
        return True
        
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        return False

def execute_schema_file(file_path: str):
    """Execute SQL schema file"""
    try:
        with open(file_path, 'r') as file:
            schema_sql = file.read()
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
        
        logger.info(f"Schema file executed successfully: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to execute schema file {file_path}: {e}")
        return False

# Query builders and utilities
class QueryBuilder:
    """Helper class for building dynamic SQL queries"""
    
    @staticmethod
    def build_select(table: str, columns: List[str] = None, where_conditions: Dict[str, Any] = None, 
                    order_by: str = None, limit: int = None, offset: int = None) -> tuple:
        """Build a SELECT query with optional conditions"""
        
        # Build columns
        if columns:
            columns_str = ', '.join(columns)
        else:
            columns_str = '*'
        
        query = f"SELECT {columns_str} FROM {table}"
        params = []
        
        # Build WHERE clause
        if where_conditions:
            where_clauses = []
            for key, value in where_conditions.items():
                if value is not None:
                    where_clauses.append(f"{key} = %s")
                    params.append(value)
                else:
                    where_clauses.append(f"{key} IS NULL")
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"
        
        # Add LIMIT and OFFSET
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"
        
        return query, tuple(params)
    
    @staticmethod
    def build_insert(table: str, data: Dict[str, Any], returning: str = None) -> tuple:
        """Build an INSERT query"""
        columns = list(data.keys())
        values = list(data.values())
        
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(values))
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        if returning:
            query += f" RETURNING {returning}"
        
        return query, tuple(values)
    
    @staticmethod
    def build_update(table: str, data: Dict[str, Any], where_conditions: Dict[str, Any], 
                    returning: str = None) -> tuple:
        """Build an UPDATE query"""
        set_clauses = []
        params = []
        
        # Build SET clause
        for key, value in data.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        
        # Build WHERE clause
        if where_conditions:
            where_clauses = []
            for key, value in where_conditions.items():
                where_clauses.append(f"{key} = %s")
                params.append(value)
            
            query += " WHERE " + " AND ".join(where_clauses)
        
        if returning:
            query += f" RETURNING {returning}"
        
        return query, tuple(params)

# Pagination helper
class Paginator:
    """Helper class for pagination"""
    
    def __init__(self, page: int = 1, per_page: int = 20, max_per_page: int = 100):
        self.page = max(1, page)
        self.per_page = min(max(1, per_page), max_per_page)
        self.offset = (self.page - 1) * self.per_page
    
    def paginate_query(self, base_query: str, params: tuple = None, count_query: str = None) -> Dict[str, Any]:
        """Execute paginated query and return results with pagination info"""
        
        # Get total count
        if count_query:
            total = db_manager.execute_single(count_query, params)['count']
        else:
            count_query = f"SELECT COUNT(*) as count FROM ({base_query}) as subquery"
            total = db_manager.execute_single(count_query, params)['count']
        
        # Get paginated results
        paginated_query = f"{base_query} LIMIT {self.per_page} OFFSET {self.offset}"
        items = db_manager.execute_query(paginated_query, params)
        
        # Calculate pagination info
        total_pages = (total + self.per_page - 1) // self.per_page
        has_prev = self.page > 1
        has_next = self.page < total_pages
        
        return {
            'items': items,
            'pagination': {
                'page': self.page,
                'per_page': self.per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': self.page - 1 if has_prev else None,
                'next_page': self.page + 1 if has_next else None
            }
        }

