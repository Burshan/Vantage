"""
Baseline Controller
Handles baseline image creation and management
"""
import logging
from flask import Blueprint, request

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, error_response, not_found_response
from shared_db import db_manager
from models import AreaOfInterest
from services.baseline_service import create_baseline_async


logger = logging.getLogger(__name__)

# Create blueprint
baseline_bp = Blueprint('baseline', __name__, url_prefix='/api/aoi')



@baseline_bp.route('/<int:aoi_id>/baseline', methods=['POST'])
@require_auth
@handle_errors
def create_baseline_manual(aoi_id):
    """Manually trigger baseline creation"""
    user_id = request.user['id']
    
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
        
        if aoi.baseline_status == 'processing':
            return error_response("Baseline creation already in progress", "BASELINE_IN_PROGRESS", 400)
    
    # Start baseline creation
    create_baseline_async(aoi_id)
    
    return success_response(
        data={'aoi_id': aoi_id},
        message="Baseline creation started"
    )


@baseline_bp.route('/<int:aoi_id>/baseline', methods=['GET'])
@require_auth
@handle_errors
def get_baseline_status(aoi_id):
    """Get baseline creation status for AOI"""
    user_id = request.user['id']
    
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
    
    return success_response(
        data={
            'aoi_id': aoi_id,
            'baseline_status': aoi.baseline_status,
            'baseline_date': aoi.baseline_date.isoformat() if aoi.baseline_date else None,
            'baseline_image_url': f'/api/image/{aoi.baseline_image_filename}' if aoi.baseline_image_filename else None
        },
        message="Baseline status retrieved successfully"
    )