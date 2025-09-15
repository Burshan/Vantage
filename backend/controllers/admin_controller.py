"""
Admin Controller
Handles admin and system-related API endpoints
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, send_file
from sqlalchemy.sql import func
import os
import re

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, error_response, not_found_response
from shared_db import db_manager
from models import User, AreaOfInterest, AnalysisHistory, UserActivity
from config import Config

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api')


@admin_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db_manager.get_session() as session:
            from sqlalchemy import text
            session.execute(text('SELECT 1'))
        
        return success_response(
            data={
                'service': 'satellite-intelligence-api',
                'version': '2.0.0',
                'environment': Config.ENVIRONMENT,
                'database': 'connected'
            },
            message="Service is healthy"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return error_response(
            f"Service is unhealthy: {str(e)}",
            "HEALTH_CHECK_FAILED",
            503
        )


@admin_bp.route('/admin/stats')
@require_auth
@handle_errors
def get_admin_stats():
    """Get system statistics"""
    user = request.user
    
    # Check if user is admin
    if not user.get('is_admin') and user.get('role') not in ['admin', 'super_admin']:
        return error_response('Admin access required', 'FORBIDDEN', 403)
    
    try:
        # Use the database manager method we created
        stats = db_manager.get_admin_stats()
        
        return success_response(
            data={'stats': stats},
            message="Admin statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        return error_response(
            f"Failed to load admin statistics: {str(e)}",
            "ADMIN_STATS_ERROR",
            500
        )


@admin_bp.route('/debug/user-status')
@require_auth
@handle_errors
def debug_user_status():
    """Debug endpoint to check user status"""
    user_dict = request.user
    user_id = user_dict['id']
    
    logger.info(f"Debug request for user: {user_dict}")
    
    # Get comprehensive user data
    with db_manager.get_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        
        aoi_count = session.query(AreaOfInterest).filter_by(
            user_id=user_id, is_active=True
        ).count()
        
        analysis_count = session.query(AnalysisHistory).filter_by(
            user_id=user_id
        ).count()
        
        recent_activity = session.query(UserActivity).filter_by(
            user_id=user_id
        ).order_by(UserActivity.timestamp.desc()).limit(5).all()
    
    return success_response(
        data={
            'request_user': user_dict,
            'db_user': user.to_dict() if user else None,
            'aoi_count': aoi_count,
            'analysis_count': analysis_count,
            'recent_activity': [activity.to_dict() for activity in recent_activity],
            'database_url': Config.DATABASE_URL.split('@')[0] + '@[HIDDEN]'
        },
        message="Debug information retrieved successfully"
    )


@admin_bp.route('/debug/ping')
def debug_ping():
    """Simple ping endpoint for debugging"""
    return success_response(
        message="Backend is responding"
    )


# Note: Image serving is now handled by controllers/image_controller.py
# The get_image function has been removed to avoid route conflicts