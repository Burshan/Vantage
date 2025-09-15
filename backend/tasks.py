from celery import Celery
from celery_app import celery_app
from datetime import datetime, timedelta
import uuid
import os
import numpy as np
from PIL import Image
import logging

# Import our existing modules
from database import DatabaseManager
from config import Config
from models import AreaOfInterest, AnalysisHistory

# Initialize components
db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
logger = logging.getLogger(__name__)

# Import satellite processor
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@celery_app.task(bind=True, name='tasks.run_scheduled_analysis')
def run_scheduled_analysis(self, aoi_id, analysis_type='baseline_comparison'):
    """
    Celery task to run scheduled analysis for an AOI
    """
    try:
        logger.info(f"🤖 Starting Celery scheduled analysis for AOI {aoi_id}")
        
        # Get AOI details
        with db_manager.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(id=aoi_id).first()
            if not aoi or not aoi.is_active:
                logger.warning(f"AOI {aoi_id} not found or inactive")
                return {'success': False, 'error': 'AOI not found or inactive'}
            
            user_id = aoi.user_id
            aoi_name = aoi.name
            bbox = aoi.bbox_coordinates
            baseline_filename = aoi.baseline_image_filename
            
        # Import satellite service here to avoid circular imports
        from services.satellite_service import SatelliteService
        satellite_processor = SatelliteService(Config.CLIENT_ID, Config.CLIENT_SECRET)
        
        # Generate date ranges
        current_date = datetime.now()
        if analysis_type == 'baseline_comparison':
            # For baseline comparison, get current image vs baseline
            date_from = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = current_date.strftime("%Y-%m-%d")
            
            # Download current image
            current_image = satellite_processor.download_image(
                bbox=bbox,
                date_from=date_from,
                date_to=date_to
            )
            
            if not current_image:
                logger.error("Failed to download current image")
                return {'success': False, 'error': 'Failed to download current image'}
            
            # Load baseline image
            baseline_path = os.path.join(Config.IMAGES_DIR, baseline_filename)
            if not os.path.exists(baseline_path):
                logger.error("Baseline image not found")
                return {'success': False, 'error': 'Baseline image not found'}
            
            baseline_image = Image.open(baseline_path)
            
            # Create filenames
            process_id = str(uuid.uuid4())[:8]
            current_filename = f"scheduled_aoi_{aoi_id}_current_{process_id}.jpg"
            heatmap_filename = f"scheduled_aoi_{aoi_id}_heatmap_{process_id}.png"
            
            current_path = os.path.join(Config.IMAGES_DIR, current_filename)
            heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
            
            # Save current image
            current_image.save(current_path, 'JPEG', quality=95)
            
            # Create heatmap
            satellite_processor.create_heatmap(baseline_image, current_image, heatmap_path)
            
            # Calculate change percentage
            change_percentage = satellite_processor.calculate_change_percentage(baseline_image, current_image)
            
            # Save to database
            analysis_id = db_manager.save_analysis(
                user_id=user_id,
                aoi_id=aoi_id,
                process_id=process_id,
                operation_name="SCHEDULED BASELINE COMPARISON",
                location_description=f"{aoi_name} - Scheduled Analysis",
                bbox_coordinates=bbox,
                image_filenames={
                    'image1': baseline_filename,  # baseline
                    'image2': current_filename,             # current
                    'heatmap': heatmap_filename
                },
                meta={
                    'analysis_date': current_date.isoformat(),
                    'comparison_type': 'baseline_vs_current',
                    'analysis_type': 'scheduled_celery',
                    'scheduled_task': True
                },
                change_percentage=change_percentage,
                tokens_used=0
            )
            
            logger.info(f"✅ Scheduled analysis completed for AOI {aoi_id} - Change: {change_percentage:.2f}%")
            
            # Check for significant change and potentially send notifications
            if change_percentage > 15.0:
                logger.warning(f"🚨 Significant change detected in {aoi_name}: {change_percentage:.2f}%")
                # Here you could add notification logic (email, webhook, etc.)
            
            # Update next run time based on frequency
            _update_next_run_time(aoi_id)
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                'change_percentage': change_percentage,
                'aoi_name': aoi_name,
                'message': f'Scheduled analysis completed for {aoi_name}'
            }
            
    except Exception as e:
        logger.error(f"❌ Scheduled analysis failed for AOI {aoi_id}: {str(e)}")
        # Don't update next run time on failure - let it retry
        return {'success': False, 'error': str(e)}

def _update_next_run_time(aoi_id):
    """Update the next run time based on frequency"""
    try:
        with db_manager.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(id=aoi_id).first()
            if not aoi:
                return
            
            frequency = aoi.monitoring_frequency
            if not frequency:
                return
            
            current_time = datetime.utcnow()
            
            if frequency == 'daily':
                aoi.next_run_at = current_time + timedelta(days=1)
            elif frequency == 'weekly':
                aoi.next_run_at = current_time + timedelta(days=7)
            elif frequency == 'monthly':
                aoi.next_run_at = current_time + timedelta(days=30)
            elif frequency == 'once':
                # For one-time tasks, disable monitoring
                aoi.monitoring_frequency = None
                aoi.next_run_at = None
            
            session.commit()
            
            # Schedule next run if there is one
            if aoi.next_run_at and frequency != 'once':
                schedule_analysis_task(aoi_id, aoi.next_run_at)
                
    except Exception as e:
        logger.error(f"Failed to update next run time for AOI {aoi_id}: {e}")

@celery_app.task(name='tasks.schedule_analysis_task')
def schedule_analysis_task(aoi_id, scheduled_time):
    """
    Schedule an analysis task to run at a specific time
    """
    try:
        # Convert to datetime if it's a string
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        
        # Schedule the task using Celery's apply_async with eta
        result = run_scheduled_analysis.apply_async(
            args=[aoi_id],
            eta=scheduled_time
        )
        
        logger.info(f"📅 Scheduled analysis task {result.id} for AOI {aoi_id} at {scheduled_time}")
        return result.id
        
    except Exception as e:
        logger.error(f"Failed to schedule analysis task: {e}")
        return None

@celery_app.task(name='tasks.cancel_scheduled_analysis')
def cancel_scheduled_analysis(task_id):
    """
    Cancel a scheduled analysis task
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"🚫 Cancelled scheduled analysis task {task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return False