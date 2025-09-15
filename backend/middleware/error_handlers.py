"""
Error Handlers Middleware
Centralized error handling for the Flask application
"""
import logging
from flask import jsonify
from utils.responses import error_response, server_error_response, not_found_response

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return not_found_response("Endpoint not found")

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal server error: {str(error)}")
        return server_error_response("Internal server error")
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return error_response("Bad request", "BAD_REQUEST", 400)
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return error_response("Unauthorized", "UNAUTHORIZED", 401)
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return error_response("Forbidden", "FORBIDDEN", 403)
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return error_response("Method not allowed", "METHOD_NOT_ALLOWED", 405)
    
    logger.info("✅ Error handlers registered successfully")