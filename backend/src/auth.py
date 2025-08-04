"""
Authentication module for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from functools import wraps
from datetime import datetime, timedelta
import jwt
from flask import request, jsonify, current_app
from src.models.user import User
from src.database import db_manager

class AuthManager:
    """Authentication manager for JWT tokens"""
    
    @staticmethod
    def generate_tokens(user: User) -> dict:
        """Generate access and refresh tokens for user"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'iat': now,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'username': user.username,
            'iat': now,
            'exp': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'type': 'refresh'
        }
        
        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
            'user': user.to_dict()
        }
    
    @staticmethod
    def verify_token(token: str, token_type: str = 'access') -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
            )
            
            # Check token type
            if payload.get('type') != token_type:
                raise jwt.InvalidTokenError(f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                raise jwt.ExpiredSignatureError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """Generate new access token from refresh token"""
        try:
            # Verify refresh token
            payload = AuthManager.verify_token(refresh_token, 'refresh')
            
            # Get user
            user = User.find_by_id(payload['user_id'])
            if not user or not user.is_active:
                raise jwt.InvalidTokenError("User not found or inactive")
            
            # Generate new access token
            now = datetime.utcnow()
            access_payload = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'iat': now,
                'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
                'type': 'access'
            }
            
            access_token = jwt.encode(
                access_payload,
                current_app.config['JWT_SECRET_KEY'],
                algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
            )
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            }
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            raise jwt.InvalidTokenError(f"Invalid refresh token: {str(e)}")
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> tuple[bool, str, User]:
        """Authenticate user with username and password"""
        try:
            # Find user by username or email
            user = User.find_by_username(username)
            if not user:
                user = User.find_by_email(username)
            
            if not user:
                return False, "Invalid username or password", None
            
            if not user.is_active:
                return False, "Account is deactivated", None
            
            # Verify password
            if not user.verify_password(password):
                return False, "Invalid username or password", None
            
            # Update last login
            user.update_last_login()
            
            return True, "Authentication successful", user
            
        except Exception as e:
            return False, f"Authentication error: {str(e)}", None

def get_token_from_header() -> str:
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        # Expected format: "Bearer <token>"
        scheme, token = auth_header.split(' ', 1)
        if scheme.lower() != 'bearer':
            return None
        return token
    except ValueError:
        return None

def get_current_user() -> User:
    """Get current authenticated user from token"""
    token = get_token_from_header()
    if not token:
        return None
    
    try:
        payload = AuthManager.verify_token(token)
        user = User.find_by_id(payload['user_id'])
        return user if user and user.is_active else None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Authorization token is required'
                }
            }), 401
        
        try:
            payload = AuthManager.verify_token(token)
            user = User.find_by_id(payload['user_id'])
            
            if not user or not user.is_active:
                return jsonify({
                    'error': {
                        'code': 'INVALID_USER',
                        'message': 'User not found or inactive'
                    }
                }), 401
            
            # Add user to request context
            request.current_user = user
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': {
                    'code': 'TOKEN_EXPIRED',
                    'message': 'Token has expired'
                }
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': f'Invalid token: {str(e)}'
                }
            }), 401
    
    return decorated_function

def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges (future use)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, all authenticated users are considered admins
        # This can be extended later with role-based access control
        return login_required(f)(*args, **kwargs)
    
    return decorated_function

# Rate limiting helpers
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.attempts = {}
    
    def is_rate_limited(self, key: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if key is rate limited"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if key in self.attempts:
            self.attempts[key] = [attempt for attempt in self.attempts[key] if attempt > window_start]
        
        # Check current attempts
        current_attempts = len(self.attempts.get(key, []))
        return current_attempts >= max_attempts
    
    def record_attempt(self, key: str):
        """Record an attempt"""
        now = datetime.utcnow()
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(now)
    
    def reset_attempts(self, key: str):
        """Reset attempts for key"""
        if key in self.attempts:
            del self.attempts[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_attempts: int = 5, window_minutes: int = 15, key_func=None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine rate limit key
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            # Check rate limit
            if rate_limiter.is_rate_limited(key, max_attempts, window_minutes):
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMITED',
                        'message': f'Too many attempts. Try again in {window_minutes} minutes.'
                    }
                }), 429
            
            # Record attempt
            rate_limiter.record_attempt(key)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Audit logging
def log_auth_event(user_id: int, action: str, ip_address: str = None, user_agent: str = None, success: bool = True):
    """Log authentication events"""
    try:
        audit_data = {
            'user_id': user_id,
            'action': action,
            'entity_type': 'users',
            'entity_id': user_id,
            'ip_address': ip_address or request.remote_addr,
            'user_agent': user_agent or request.headers.get('User-Agent'),
            'new_values': {'success': success, 'timestamp': datetime.utcnow().isoformat()}
        }
        
        query = """
        INSERT INTO audit_log (user_id, action, entity_type, entity_id, ip_address, user_agent, new_values)
        VALUES (%(user_id)s, %(action)s, %(entity_type)s, %(entity_id)s, %(ip_address)s, %(user_agent)s, %(new_values)s)
        """
        
        db_manager.execute_update(query, audit_data)
        
    except Exception:
        # Don't fail the request if audit logging fails
        pass

