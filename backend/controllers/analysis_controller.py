"""
Analysis Controller
Handles all analysis-related API endpoints
"""
import logging
import uuid
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, error_response, not_found_response
from utils.date_strategy import SatelliteDateStrategy
from shared_db import db_manager
from models import AreaOfInterest
from config import Config


logger = logging.getLogger(__name__)

# Create blueprint
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# Satellite service will be accessed from Flask app context
# (No global service instance - use app.satellite_service instead)


@analysis_bp.route('/process-satellite-images', methods=['POST'])
@require_auth
@handle_errors
def process_satellite_images():
    """Process satellite images - for manual analysis without AOI"""
    user_dict = request.user
    user_id = user_dict['id']
    data = request.get_json() or {}
    
    logger.info(f"Starting manual satellite analysis for user: {user_dict.get('email', user_id)}")
    
    # Get updated user data
    updated_user = db_manager.get_user_by_id(user_id)
    
    # Default coordinates for manual analysis
    bbox = data.get('bbox_coordinates', [50.964594, 34.876149, 51.025335, 34.911741])
    location_description = data.get('location_description', "Manual Analysis")
    
    # Get intelligent date ranges for comparison using date strategy
    if 'date1_from' in data and 'date1_to' in data and 'date2_from' in data and 'date2_to' in data:
        # Use provided dates
        date1_from = data['date1_from']
        date1_to = data['date1_to']
        date2_from = data['date2_from']
        date2_to = data['date2_to']
    else:
        # Use intelligent date strategy
        dates = SatelliteDateStrategy.get_manual_comparison_dates()
        date1_from = dates['date1_from']
        date1_to = dates['date1_to']
        date2_from = dates['date2_from']
        date2_to = dates['date2_to']
    
    process_id = str(uuid.uuid4())[:8]
    
    # Download images
    image1 = current_app.satellite_service.download_image(bbox, date1_from, date1_to)
    if not image1:
        return error_response("Failed to download first image", "DOWNLOAD_ERROR", 500)
    
    image2 = current_app.satellite_service.download_image(bbox, date2_from, date2_to)
    if not image2:
        return error_response("Failed to download second image", "DOWNLOAD_ERROR", 500)
    
    # Create filenames
    image1_filename = f"manual_{user_id}_image1_{process_id}.jpg"
    image2_filename = f"manual_{user_id}_image2_{process_id}.jpg"
    heatmap_filename = f"manual_{user_id}_heatmap_{process_id}.png"
    
    # Save images (returns dict with local_path and s3_key)
    image1_result = current_app.satellite_service.save_image(image1, image1_filename)
    image2_result = current_app.satellite_service.save_image(image2, image2_filename)
    
    # Create heatmap
    heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
    heatmap_result = current_app.satellite_service.create_heatmap(image1, image2, heatmap_path)
    
    # Calculate change percentage
    change_percentage = current_app.satellite_service.calculate_change_percentage(image1, image2)
    
    # Save to database
    analysis_id = db_manager.save_analysis(
        user_id=user_id,
        aoi_id=None,  # Manual analysis not tied to AOI
        process_id=process_id,
        operation_name="MANUAL COMPARISON",
        location_description=location_description,
        bbox_coordinates=bbox,
        image_filenames={
            'image1': image1_filename,
            'image2': image2_filename,
            'heatmap': heatmap_filename
        },
        s3_keys={
            'image1': image1_result.get('s3_key') if isinstance(image1_result, dict) else None,
            'image2': image2_result.get('s3_key') if isinstance(image2_result, dict) else None,
            'heatmap': heatmap_result.get('s3_key') if isinstance(heatmap_result, dict) else None
        },
        meta={
            'date1_from': date1_from,
            'date1_to': date1_to,
            'date2_from': date2_from,
            'date2_to': date2_to,
            'processing_time': datetime.now().isoformat()
        },
        change_percentage=change_percentage,
        tokens_used=0
    )
    
    return success_response(
        data={
            'analysis_id': analysis_id,
            'process_id': process_id,
            'change_percentage': round(change_percentage, 2),
            'user_tokens': {
                'tokens_remaining': updated_user['tokens_remaining'],
                'tokens_used_this_session': 0
            },
            'images': {
                'baseline_url': f'/api/image/{image1_filename}',
                'current_url': f'/api/image/{image2_filename}',
                'heatmap_url': f'/api/image/{heatmap_filename}'
            }
        },
        message="Images processed successfully"
    )


@analysis_bp.route('/aoi/<int:aoi_id>/run-analysis', methods=['POST'])
@require_auth
@handle_errors  
def run_aoi_analysis_manual(aoi_id):
    """Manually trigger analysis for AOI (separate from dashboard view)"""
    user_dict = request.user
    user_id = user_dict['id']
    
    logger.info(f"Manual analysis triggered for AOI {aoi_id} by user {user_id}")
    
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
        
        if aoi.baseline_status != 'completed':
            return error_response(
                "Please wait for baseline creation to complete before running analysis",
                "BASELINE_NOT_READY",
                400,
                details={'baseline_status': aoi.baseline_status}
            )
    
    # Get request parameters
    request_data = request.get_json() or {}
    analysis_type = request_data.get('analysis_type', 'baseline_comparison')  # baseline_comparison, time_range
    
    if analysis_type == 'baseline_comparison':
        # Compare with baseline (current vs baseline)
        return _run_baseline_comparison_analysis(aoi_id, user_id)
    else:
        # Custom time range comparison
        return _run_time_range_analysis(aoi_id, user_id, request_data)


def _run_baseline_comparison_analysis(aoi_id, user_id):
    """Run analysis comparing current image with baseline"""
    # Check tokens and consume them first
    success, message = db_manager.use_token(user_id, 1, f"Manual baseline analysis AOI {aoi_id}")
    if not success:
        return error_response(message, "INSUFFICIENT_TOKENS", 400)
    
    # Fresh session to fetch AOI
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
        
        # Use rolling window date strategy for current image
        dates = SatelliteDateStrategy.get_analysis_dates()
        date_from = dates['current_from']
        date_to = dates['current_to']
        
        process_id = str(uuid.uuid4())[:8]
        
        # Download current image
        current_image = current_app.satellite_service.download_image(
            bbox=aoi.bbox_coordinates,
            date_from=date_from,
            date_to=date_to
        )
        
        if not current_image:
            return error_response("Failed to download current image", "DOWNLOAD_ERROR", 500)
        
        # Load baseline image
        baseline_image = current_app.satellite_service.load_baseline_image(aoi.baseline_image_filename)
        if not baseline_image:
            return error_response("Baseline image not found", "BASELINE_ERROR", 500)
        
        # Create filenames
        current_filename = f"aoi_{aoi.id}_current_{process_id}.jpg"
        heatmap_filename = f"aoi_{aoi.id}_heatmap_{process_id}.png"
        
        # Save current image
        current_result = current_app.satellite_service.save_image(current_image, current_filename, aoi.id)
        
        # Create heatmap
        heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
        heatmap_result = current_app.satellite_service.create_heatmap(baseline_image, current_image, heatmap_path, aoi.id)
        
        # Calculate change percentage
        change_percentage = current_app.satellite_service.calculate_change_percentage(baseline_image, current_image)
        
        # Save to database
        analysis_id = db_manager.save_analysis(
            user_id=user_id,
            aoi_id=aoi.id,
            process_id=process_id,
            operation_name="BASELINE COMPARISON",
            location_description=f"{aoi.name} - {aoi.location_name}",
            bbox_coordinates=aoi.bbox_coordinates,
            image_filenames={
                'image1': aoi.baseline_image_filename,  # baseline
                'image2': current_filename,             # current
                'heatmap': heatmap_filename
            },
            s3_keys={
                'image1': None,  # baseline images not yet migrated to S3
                'image2': current_result.get('s3_key') if isinstance(current_result, dict) else None,
                'heatmap': heatmap_result.get('s3_key') if isinstance(heatmap_result, dict) else None
            },
            meta={
                'analysis_date': datetime.now().isoformat(),
                'comparison_type': 'baseline_vs_current',
                'analysis_type': 'manual_trigger'
            },
            change_percentage=change_percentage,
            tokens_used=1
        )
        
        # Get updated user data
        updated_user = db_manager.get_user_by_id(user_id)
        
        return success_response(
            data={
                'analysis_id': analysis_id,
                'process_id': process_id,
                'change_percentage': round(change_percentage, 2),
                'user_tokens': {
                    'tokens_remaining': updated_user['tokens_remaining'],
                    'tokens_used_this_session': 1
                },
                'images': {
                    'baseline_url': f'/api/image/{aoi.baseline_image_filename}',
                    'current_url': f'/api/image/{current_filename}',
                    'heatmap_url': f'/api/image/{heatmap_filename}'
                }
            },
            message="Analysis completed successfully"
        )


def _run_time_range_analysis(aoi_id, user_id, request_data):
    """Run analysis between two time ranges"""
    # Check tokens and consume them first
    success, message = db_manager.use_token(user_id, 1, f"Manual time range analysis AOI {aoi_id}")
    if not success:
        return error_response(message, "INSUFFICIENT_TOKENS", 400)
    
    # Fresh session to fetch AOI
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return not_found_response("AOI not found")
        
        # Get date ranges from request
        date1_from = request_data.get('date1_from')
        date1_to = request_data.get('date1_to')
        date2_from = request_data.get('date2_from')
        date2_to = request_data.get('date2_to')
        
        if not all([date1_from, date1_to, date2_from, date2_to]):
            return error_response(
                "All date ranges are required for time range analysis",
                "VALIDATION_ERROR",
                400
            )
        
        process_id = str(uuid.uuid4())[:8]
        
        # Download both images
        image1 = current_app.satellite_service.download_image(aoi.bbox_coordinates, date1_from, date1_to)
        image2 = current_app.satellite_service.download_image(aoi.bbox_coordinates, date2_from, date2_to)
        
        if not image1 or not image2:
            return error_response("Failed to download one or both images", "DOWNLOAD_ERROR", 500)
        
        # Create filenames
        image1_filename = f"aoi_{aoi.id}_period1_{process_id}.jpg"
        image2_filename = f"aoi_{aoi.id}_period2_{process_id}.jpg"
        heatmap_filename = f"aoi_{aoi.id}_comparison_{process_id}.png"
        
        # Save images
        image1_result = current_app.satellite_service.save_image(image1, image1_filename, aoi.id)
        image2_result = current_app.satellite_service.save_image(image2, image2_filename, aoi.id)
        
        # Create heatmap
        heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
        heatmap_result = current_app.satellite_service.create_heatmap(image1, image2, heatmap_path, aoi.id)
        
        # Calculate change percentage
        change_percentage = current_app.satellite_service.calculate_change_percentage(image1, image2)
        
        # Save to database
        analysis_id = db_manager.save_analysis(
            user_id=user_id,
            aoi_id=aoi.id,
            process_id=process_id,
            operation_name="TIME RANGE COMPARISON",
            location_description=f"{aoi.name} - {aoi.location_name}",
            bbox_coordinates=aoi.bbox_coordinates,
            image_filenames={
                'image1': image1_filename,
                'image2': image2_filename,
                'heatmap': heatmap_filename
            },
            s3_keys={
                'image1': image1_result.get('s3_key') if isinstance(image1_result, dict) else None,
                'image2': image2_result.get('s3_key') if isinstance(image2_result, dict) else None,
                'heatmap': heatmap_result.get('s3_key') if isinstance(heatmap_result, dict) else None
            },
            meta={
                'analysis_date': datetime.now().isoformat(),
                'comparison_type': 'time_range',
                'period1': f"{date1_from} to {date1_to}",
                'period2': f"{date2_from} to {date2_to}",
                'analysis_type': 'manual_trigger'
            },
            change_percentage=change_percentage,
            tokens_used=1
        )
        
        # Get updated user data
        updated_user = db_manager.get_user_by_id(user_id)
        
        return success_response(
            data={
                'analysis_id': analysis_id,
                'process_id': process_id,
                'change_percentage': round(change_percentage, 2),
                'user_tokens': {
                    'tokens_remaining': updated_user['tokens_remaining'],
                    'tokens_used_this_session': 1
                },
                'images': {
                    'baseline_url': f'/api/image/{image1_filename}',
                    'current_url': f'/api/image/{image2_filename}',
                    'heatmap_url': f'/api/image/{heatmap_filename}'
                }
            },
            message="Time range analysis completed successfully"
        )