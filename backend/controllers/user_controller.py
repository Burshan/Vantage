"""
User Controller
Handles user-related API endpoints
"""
import logging
from flask import Blueprint, request

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, not_found_response
from shared_db import db_manager
from config import Config

logger = logging.getLogger(__name__)

# Create blueprint
user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/profile')
@require_auth
@handle_errors
def get_user_profile():
    """Get comprehensive user profile"""
    user_dict = request.user
    user_id = user_dict['id']
    
    logger.info(f"Getting profile for user ID: {user_id}")
    
    # Get fresh user data from database
    fresh_user = db_manager.get_user_by_id(user_id)
    if not fresh_user:
        logger.error("User not found in database!")
        return not_found_response("User not found")
    
    # Get recent history
    history = db_manager.get_user_history(user_id, limit=5)
    
    logger.info(f"Sending profile response: tokens_remaining={fresh_user['tokens_remaining']}")
    
    return success_response(
        data={
            'user': {
                'id': fresh_user['id'],
                'email': fresh_user['email'],
                'first_name': fresh_user['first_name'],
                'last_name': fresh_user['last_name'],
                'role': fresh_user.get('role', 'user'),
                'is_admin': fresh_user.get('is_admin', False),
                'tokens_remaining': fresh_user['tokens_remaining'],
                'total_tokens_used': fresh_user['total_tokens_used'],
                'created_at': fresh_user.get('created_at'),
                'updated_at': fresh_user.get('updated_at')
            },
            'recent_history': history,
            'system_info': {
                'environment': Config.ENVIRONMENT,
                'database_type': 'PostgreSQL' if 'postgresql' in Config.DATABASE_URL else 'SQLite'
            }
        },
        message="User profile retrieved successfully"
    )


@user_bp.route('/history')
@require_auth
@handle_errors
def get_user_history():
    """Get user's full analysis history"""
    user_id = request.user['id']
    limit = request.args.get('limit', 20, type=int)
    
    # Validate limit
    if limit < 1 or limit > 100:
        limit = 20
    
    history = db_manager.get_user_history(user_id, limit=limit)
    
    return success_response(
        data={
            'history': history,
            'total_analyses': len(history)
        },
        message="User history retrieved successfully"
    )