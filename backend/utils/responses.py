"""
Standardized API response utilities
"""
from flask import jsonify
from datetime import datetime


def success_response(data=None, message="Success", status_code=200):
    """Create a standardized success response"""
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def error_response(message="An error occurred", code="ERROR", status_code=400, details=None):
    """Create a standardized error response"""
    response = {
        'success': False,
        'error': message,
        'code': code,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def validation_error_response(message="Validation failed", errors=None):
    """Create a validation error response"""
    return error_response(
        message=message, 
        code="VALIDATION_ERROR", 
        status_code=400, 
        details=errors
    )


def auth_error_response(message="Authentication required"):
    """Create an authentication error response"""
    return error_response(
        message=message, 
        code="AUTH_ERROR", 
        status_code=401
    )


def forbidden_response(message="Access denied"):
    """Create a forbidden response"""
    return error_response(
        message=message, 
        code="FORBIDDEN", 
        status_code=403
    )


def not_found_response(message="Resource not found"):
    """Create a not found response"""
    return error_response(
        message=message, 
        code="NOT_FOUND", 
        status_code=404
    )


def server_error_response(message="Internal server error"):
    """Create a server error response"""
    return error_response(
        message=message, 
        code="INTERNAL_ERROR", 
        status_code=500
    )