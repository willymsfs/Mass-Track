"""
Authentication routes for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

from flask import Blueprint, request, jsonify
import jwt
from src.auth import AuthManager, login_required, rate_limit, log_auth_event
from src.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_attempts=5, window_minutes=15)
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'error': {
                    'code': 'MISSING_CREDENTIALS',
                    'message': 'Username and password are required'
                }
            }), 400
        
        # Authenticate user
        success, message, user = AuthManager.authenticate_user(username, password)
        
        if not success:
            # Log failed attempt
            if user:
                log_auth_event(user.id, 'login_failed', success=False)
            
            return jsonify({
                'error': {
                    'code': 'AUTHENTICATION_FAILED',
                    'message': message
                }
            }), 401
        
        # Generate tokens
        tokens = AuthManager.generate_tokens(user)
        
        # Log successful login
        log_auth_event(user.id, 'login_success', success=True)
        
        return jsonify({
            'message': 'Login successful',
            'data': tokens
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOGIN_ERROR',
                'message': f'Login failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@rate_limit(max_attempts=10, window_minutes=15)
def refresh_token():
    """Refresh access token endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        refresh_token = data.get('refresh_token', '').strip()
        
        if not refresh_token:
            return jsonify({
                'error': {
                    'code': 'MISSING_REFRESH_TOKEN',
                    'message': 'Refresh token is required'
                }
            }), 400
        
        # Refresh access token
        new_tokens = AuthManager.refresh_access_token(refresh_token)
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'data': new_tokens
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({
            'error': {
                'code': 'REFRESH_TOKEN_EXPIRED',
                'message': 'Refresh token has expired. Please login again.'
            }
        }), 401
    except jwt.InvalidTokenError as e:
        return jsonify({
            'error': {
                'code': 'INVALID_REFRESH_TOKEN',
                'message': f'Invalid refresh token: {str(e)}'
            }
        }), 401
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'REFRESH_ERROR',
                'message': f'Token refresh failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint"""
    try:
        user = request.current_user
        
        # Log logout event
        log_auth_event(user.id, 'logout', success=True)
        
        # Note: In a production system, you might want to:
        # 1. Blacklist the current token
        # 2. Store token blacklist in Redis/database
        # 3. Check blacklist in token verification
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOGOUT_ERROR',
                'message': f'Logout failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/register', methods=['POST'])
@rate_limit(max_attempts=3, window_minutes=60)
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Required fields
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not all([username, email, password, full_name]):
            return jsonify({
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Username, email, password, and full name are required'
                }
            }), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'error': {
                    'code': 'WEAK_PASSWORD',
                    'message': 'Password must be at least 8 characters long'
                }
            }), 400
        
        # Check if username already exists
        existing_user = User.find_by_username(username)
        if existing_user:
            return jsonify({
                'error': {
                    'code': 'USERNAME_EXISTS',
                    'message': 'Username already exists'
                }
            }), 409
        
        # Check if email already exists
        existing_email = User.find_by_email(email)
        if existing_email:
            return jsonify({
                'error': {
                    'code': 'EMAIL_EXISTS',
                    'message': 'Email already exists'
                }
            }), 409
        
        # Optional fields
        optional_fields = {
            'ordination_date': data.get('ordination_date'),
            'current_assignment': data.get('current_assignment'),
            'diocese': data.get('diocese'),
            'province': data.get('province'),
            'phone': data.get('phone'),
            'address': data.get('address')
        }
        
        # Create user
        user = User.create(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            **optional_fields
        )
        
        if not user:
            return jsonify({
                'error': {
                    'code': 'REGISTRATION_FAILED',
                    'message': 'Failed to create user account'
                }
            }), 500
        
        # Log registration
        log_auth_event(user.id, 'registration', success=True)
        
        # Generate tokens for immediate login
        tokens = AuthManager.generate_tokens(user)
        
        return jsonify({
            'message': 'Registration successful',
            'data': tokens
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'REGISTRATION_ERROR',
                'message': f'Registration failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        user = request.current_user
        
        return jsonify({
            'message': 'User information retrieved successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'USER_INFO_ERROR',
                'message': f'Failed to get user information: {str(e)}'
            }
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
@rate_limit(max_attempts=5, window_minutes=30)
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({
                'error': {
                    'code': 'MISSING_PASSWORDS',
                    'message': 'Current password and new password are required'
                }
            }), 400
        
        user = request.current_user
        
        # Verify current password
        if not user.verify_password(current_password):
            log_auth_event(user.id, 'password_change_failed', success=False)
            return jsonify({
                'error': {
                    'code': 'INVALID_CURRENT_PASSWORD',
                    'message': 'Current password is incorrect'
                }
            }), 401
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({
                'error': {
                    'code': 'WEAK_PASSWORD',
                    'message': 'New password must be at least 8 characters long'
                }
            }), 400
        
        # Update password
        success = user.update_password(new_password)
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'PASSWORD_UPDATE_FAILED',
                    'message': 'Failed to update password'
                }
            }), 500
        
        # Log successful password change
        log_auth_event(user.id, 'password_change_success', success=True)
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'PASSWORD_CHANGE_ERROR',
                'message': f'Password change failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify token validity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({
                'error': {
                    'code': 'MISSING_TOKEN',
                    'message': 'Token is required'
                }
            }), 400
        
        # Verify token
        payload = AuthManager.verify_token(token)
        
        # Get user
        user = User.find_by_id(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({
                'valid': False,
                'error': 'User not found or inactive'
            }), 200
        
        return jsonify({
            'valid': True,
            'user': user.to_dict(),
            'expires_at': payload['exp']
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({
            'valid': False,
            'error': 'Token has expired'
        }), 200
    except jwt.InvalidTokenError as e:
        return jsonify({
            'valid': False,
            'error': f'Invalid token: {str(e)}'
        }), 200
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'TOKEN_VERIFICATION_ERROR',
                'message': f'Token verification failed: {str(e)}'
            }
        }), 500

