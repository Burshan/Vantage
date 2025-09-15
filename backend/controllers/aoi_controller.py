"""
AOI (Area of Interest) Controller
Handles all AOI-related API endpoints
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, error_response, not_found_response
from shared_db import db_manager
from models import AreaOfInterest

logger = logging.getLogger(__name__)

# Create blueprint
aoi_bp = Blueprint('aoi', __name__, url_prefix='/api/aoi')



@aoi_bp.route('', methods=['GET'])
@require_auth
@handle_errors
def get_aois():
    """Get user's Areas of Interest with dashboard info"""
    user_id = request.user['id']
    aois = db_manager.get_user_aois(user_id)
    
    return success_response(
        data={
            'areas_of_interest': aois,
            'total_count': len(aois)
        },
        message="AOIs retrieved successfully"
    )


@aoi_bp.route('', methods=['POST'])
@require_auth
@handle_errors
def create_aoi():
    """Create a new Area of Interest with automatic baseline creation"""
    user_dict = request.user
    user_id = user_dict['id']
    aoi_data = request.get_json()
    
    logger.info(f"Create AOI request from user {user_id}")
    logger.debug(f"Request data: {aoi_data}")
    
    # Check if user has tokens (1 token per AOI)
    if user_dict['tokens_remaining'] <= 0:
        return error_response(
            "No tokens remaining. You need 1 token to create an AOI.",
            "INSUFFICIENT_TOKENS",
            402
        )
    
    # Validate required fields
    if not aoi_data.get('name'):
        return error_response("AOI name is required", "VALIDATION_ERROR", 400)
    
    bbox_coords = aoi_data.get('bbox_coordinates')
    if not bbox_coords or not isinstance(bbox_coords, list) or len(bbox_coords) != 4:
        return error_response(
            "Valid bbox coordinates are required: [lat_min, lon_min, lat_max, lon_max]", 
            "VALIDATION_ERROR", 
            400
        )

    lat_min, lon_min, lat_max, lon_max = bbox_coords

    # Validation
    if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
        return error_response("Latitude values must be between -90 and 90", "VALIDATION_ERROR", 400)
    if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
        return error_response("Longitude values must be between -180 and 180", "VALIDATION_ERROR", 400)
    if lat_min >= lat_max or lon_min >= lon_max:
        return error_response("Invalid bounding box: min values must be less than max values", "VALIDATION_ERROR", 400)

    # Convert to Sentinel order before saving
    aoi_data['bbox_coordinates'] = [lon_min, lat_min, lon_max, lat_max]
    
    logger.info("Validation passed, consuming token and creating AOI...")
    
    # Consume 1 token for AOI creation
    success, message = db_manager.use_token(user_id, 1)
    if not success:
        return error_response(message, "TOKEN_ERROR", 402)
    
    # Create AOI
    aoi_id = db_manager.create_aoi(user_id, aoi_data)
    
    # Start baseline creation in background
    from services.baseline_service import create_baseline_async
    create_baseline_async(aoi_id)
    
    logger.info(f"AOI created successfully with ID: {aoi_id}")
    
    # Get updated user profile to return current token count
    updated_user = db_manager.get_user_by_id(user_id)
    
    return success_response(
        data={
            'aoi_id': aoi_id,
            'baseline_status': 'pending',
            'tokens_remaining': updated_user['tokens_remaining']
        },
        message="AOI created successfully. 1 token consumed. Baseline image creation started."
    )


@aoi_bp.route('/<int:aoi_id>', methods=['DELETE'])
@require_auth
@handle_errors
def delete_aoi(aoi_id):
    """Delete an Area of Interest"""
    user_id = request.user['id']
    success, message = db_manager.delete_aoi(user_id, aoi_id)
    
    if success:
        return success_response(message=message)
    else:
        return not_found_response(message)


@aoi_bp.route('/<int:aoi_id>', methods=['GET'])
@require_auth
@handle_errors
def get_aoi_dashboard(aoi_id):
    """Get comprehensive AOI dashboard"""
    user_id = request.user['id']
    
    dashboard_data = db_manager.get_aoi_dashboard(aoi_id, user_id)
    if not dashboard_data:
        return not_found_response("AOI not found or access denied")
    
    return success_response(
        data={'dashboard': dashboard_data},
        message="AOI dashboard retrieved successfully"
    )


@aoi_bp.route('/<int:aoi_id>/dashboard', methods=['GET'])
@require_auth
@handle_errors
def get_aoi_dashboard_view(aoi_id):
    """Get AOI dashboard for viewing only - no analysis execution"""
    user_id = request.user['id']
    
    logger.info(f"Getting dashboard view for AOI {aoi_id}, user {user_id}")
    
    with db_manager.get_session() as session:
        from sqlalchemy.sql import func
        from models import AnalysisHistory
        
        # Get AOI details
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
        
        # Get analysis history (last 10 analyses)
        analyses = session.query(AnalysisHistory).filter_by(
            aoi_id=aoi_id
        ).order_by(AnalysisHistory.analysis_timestamp.desc()).limit(10).all()
        
        # Get statistics
        total_analyses = session.query(AnalysisHistory).filter_by(aoi_id=aoi_id).count()
        total_tokens_used = session.query(func.sum(AnalysisHistory.tokens_used)).filter_by(aoi_id=aoi_id).scalar() or 0
        
        # Get latest analysis for quick view
        latest_analysis = analyses[0] if analyses else None
        
        # Calculate monitoring status
        last_analysis_date = latest_analysis.analysis_timestamp if latest_analysis else None
        monitoring_status = "active" if latest_analysis and (
            datetime.now() - latest_analysis.analysis_timestamp
        ).days < 30 else "idle"
        
        dashboard_data = {
            'aoi': {
                'id': aoi.id,
                'name': aoi.name,
                'description': aoi.description,
                'location_name': aoi.location_name,
                'bbox_coordinates': aoi.bbox_coordinates,
                'classification': aoi.classification,
                'priority': aoi.priority,
                'color_code': aoi.color_code,
                'monitoring_frequency': aoi.monitoring_frequency,
                'baseline_status': aoi.baseline_status,
                'baseline_date': aoi.baseline_date.isoformat() if aoi.baseline_date else None,
                'created_at': aoi.created_at.isoformat() if aoi.created_at else None
            },
            'statistics': {
                'total_analyses': total_analyses,
                'total_tokens_used': total_tokens_used,
                'monitoring_status': monitoring_status,
                'last_analysis_date': last_analysis_date.isoformat() if last_analysis_date else None
            },
            'baseline': {
                'status': aoi.baseline_status,
                'image_url': f'/api/image/{aoi.baseline_image_filename}' if aoi.baseline_image_filename else None,
                'date': aoi.baseline_date.isoformat() if aoi.baseline_date else None
            },
            'recent_analyses': [
                {
                    'id': analysis.id,
                    'process_id': analysis.process_id,
                    'operation_name': analysis.operation_name,
                    'analysis_timestamp': analysis.analysis_timestamp.isoformat(),
                    'change_percentage': analysis.change_percentage,
                    'tokens_used': analysis.tokens_used,
                    'images': {
                        'baseline_url': f'/api/image/{analysis.image1_filename}' if analysis.image1_filename else None,
                        'current_url': f'/api/image/{analysis.image2_filename}' if analysis.image2_filename else None,
                        'heatmap_url': f'/api/image/{analysis.heatmap_filename}' if analysis.heatmap_filename else None
                    }
                } for analysis in analyses
            ],
            'actions_available': {
                'can_run_analysis': aoi.baseline_status == 'completed',
                'can_schedule_monitoring': True,
                'can_update_baseline': True
            }
        }
    
    return success_response(
        data={'dashboard': dashboard_data},
        message="AOI dashboard retrieved successfully"
    )


@aoi_bp.route('/<int:aoi_id>/history')
@require_auth
@handle_errors
def get_aoi_history(aoi_id):
    """Get analysis history for specific AOI"""
    user_id = request.user['id']
    limit = request.args.get('limit', 20, type=int)
    
    with db_manager.get_session() as session:
        from models import AnalysisHistory
        
        # Verify access
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
        
        # Get analysis history
        analyses = session.query(AnalysisHistory).filter_by(
            aoi_id=aoi_id
        ).order_by(AnalysisHistory.analysis_timestamp.desc()).limit(limit).all()
    
    return success_response(
        data={
            'aoi_id': aoi_id,
            'aoi_name': aoi.name,
            'analyses': [analysis.to_dict() for analysis in analyses],
            'total_count': len(analyses)
        },
        message="AOI analysis history retrieved successfully"
    )