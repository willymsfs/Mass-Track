"""
Main Flask application for Mass Tracking System
Author: Manus AI
Date: January 8, 2025
"""

import os
import sys
import logging
from datetime import datetime

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.config import get_config
from src.database import init_database, validate_database_connection

# Import route blueprints
from src.routes.auth import auth_bp
from src.routes.users import users_bp
from src.routes.mass_celebrations import mass_celebrations_bp
from src.routes.bulk_intentions import bulk_intentions_bp
from src.routes.notifications import notifications_bp
from src.routes.dashboard import dashboard_bp
from src.routes.excel_import import excel_import_bp

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Initialize CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']))
    
    # Initialize database
    init_database(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(mass_celebrations_bp, url_prefix='/api/mass-celebrations')
    app.register_blueprint(bulk_intentions_bp, url_prefix='/api/bulk-intentions')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(excel_import_bp, url_prefix='/api/excel-import')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        try:
            db_status = validate_database_connection()
            return jsonify({
                'status': 'healthy' if db_status else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': app.config.get('APP_VERSION', '1.0.0'),
                'database': 'connected' if db_status else 'disconnected'
            }), 200 if db_status else 503
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500
    
    # API info endpoint
    @app.route('/api/info')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'name': app.config.get('APP_NAME', 'Mass Tracking System'),
            'version': app.config.get('APP_VERSION', '1.0.0'),
            'description': 'REST API for Catholic priest mass tracking and intention management',
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users',
                'mass_celebrations': '/api/mass-celebrations',
                'bulk_intentions': '/api/bulk-intentions',
                'notifications': '/api/notifications',
                'dashboard': '/api/dashboard',
                'excel_import': '/api/excel-import',
                'health': '/api/health'
            },
            'documentation': '/api/docs'  # Future: API documentation
        })
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': 'Bad request'
            }
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Access forbidden'
            }
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'Method not allowed'
            }
        }), 405
    
    @app.errorhandler(429)
    def rate_limited(error):
        return jsonify({
            'error': {
                'code': 'RATE_LIMITED',
                'message': 'Rate limit exceeded'
            }
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            }
        }), 500
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        if app.config.get('DEBUG'):
            app.logger.debug(f'{request.method} {request.url} - {request.remote_addr}')
    
    @app.after_request
    def log_response_info(response):
        if app.config.get('DEBUG'):
            app.logger.debug(f'Response: {response.status_code}')
        return response
    
    # Frontend serving routes
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve frontend application"""
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return jsonify({
                'error': {
                    'code': 'STATIC_FOLDER_NOT_CONFIGURED',
                    'message': 'Static folder not configured'
                }
            }), 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({
                    'message': 'Mass Tracking System API',
                    'version': app.config.get('APP_VERSION', '1.0.0'),
                    'endpoints': '/api/info'
                })
    
    return app

def setup_logging(app):
    """Setup application logging"""
    if not app.debug:
        # Production logging
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
        
        # File handler
        log_file = app.config.get('LOG_FILE', 'logs/app.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(log_level)
        
        app.logger.info('Mass Tracking System startup')

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=True)

