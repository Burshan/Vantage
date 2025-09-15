"""
Schedule Controller
Handles scheduling and monitoring API endpoints
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request

from utils.decorators import require_auth, handle_errors
from utils.responses import success_response, error_response, not_found_response
from shared_db import db_manager
from models import AreaOfInterest


logger = logging.getLogger(__name__)

# Create blueprint
schedule_bp = Blueprint('schedule', __name__, url_prefix='/api')



@schedule_bp.route('/aoi/<int:aoi_id>/schedule-monitoring', methods=['GET','POST','DELETE','OPTIONS'])
@require_auth
@handle_errors
def schedule_monitoring(aoi_id):
    """Handle schedule monitoring for AOI"""
    
    # EXTREMELY VERBOSE LOGGING
    print(f"🚨🚨🚨 SCHEDULE API CALLED! AOI={aoi_id}, METHOD={request.method}")
    logger.error(f"🚨🚨🚨 SCHEDULE API CALLED! AOI={aoi_id}, METHOD={request.method}")
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        print(f"🚨 OPTIONS request for AOI {aoi_id}")
        return '', 204
        
    user_id = request.user['id']
    print(f"🚨 USER_ID: {user_id}")
    logger.error(f"🚨 USER_ID: {user_id}")
    
    # Verify access
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(id=aoi_id, user_id=user_id).first()
        if not aoi:
            return not_found_response("AOI not found")

        if request.method == 'GET':
            return success_response(
                data={
                    'aoi_id': aoi_id,
                    'monitoring_frequency': aoi.monitoring_frequency,
                    'next_run_at': aoi.next_run_at.isoformat() if getattr(aoi, 'next_run_at', None) else None,
                    'is_active': aoi.is_active,
                    'has_schedule': aoi.next_run_at is not None
                },
                message="Schedule information retrieved successfully"
            )

        if request.method == 'POST':
            payload = request.get_json() or {}
            freq = payload.get('frequency', payload.get('monitoring_frequency'))
            enabled = payload.get('enabled', True)
            scheduled_at = payload.get('scheduled_at')  # ISO datetime string
            
            logger.info(f"🔍 Schedule request for AOI {aoi_id}: enabled={enabled}, freq={freq}, scheduled_at={scheduled_at}")
            logger.info(f"📦 Full payload: {payload}")
            
            # Log current AOI state before changes
            logger.info(f"📊 AOI {aoi_id} current state: freq={aoi.monitoring_frequency}, next_run={aoi.next_run_at}, active={aoi.is_active}")
            
            # Handle different scenarios based on enabled and frequency
            if enabled and not freq:
                logger.error(f"❌ Missing frequency parameter for AOI {aoi_id}: {payload}")
                return error_response("frequency parameter is required when enabling schedule", "VALIDATION_ERROR", 400)

            # Check if this is a disable/remove request
            if not enabled or freq == 'none':
                logger.info(f"🗑️ Disabling/removing schedule for AOI {aoi_id}")
                aoi.monitoring_frequency = None
                aoi.next_run_at = None
                # Keep AOI active, just remove schedule
            else:
                # This is an enable/create request
                aoi.monitoring_frequency = freq
                aoi.is_active = True
                
                # Set next run time based on scheduled_at or frequency
                if scheduled_at:
                    try:
                        # Handle various datetime formats
                        logger.info(f"🕐 Raw scheduled_at input: '{scheduled_at}'")
                        clean_scheduled_at = scheduled_at.replace('Z', '+00:00')
                        logger.info(f"🕐 Cleaned scheduled_at: '{clean_scheduled_at}'")
                        parsed_time = datetime.fromisoformat(clean_scheduled_at)
                        logger.info(f"🕐 Parsed with timezone: {parsed_time} (tzinfo: {parsed_time.tzinfo})")
                        
                        # Convert to UTC if it has timezone info
                        if parsed_time.tzinfo is not None:
                            utc_time = parsed_time.utctimetuple()
                            parsed_time = datetime(*utc_time[:6])
                            logger.info(f"🕐 Converted to UTC: {parsed_time}")
                        
                        aoi.next_run_at = parsed_time
                        logger.info(f"🕐 Final stored time: {aoi.next_run_at}")
                        
                        # Also log current server time for comparison
                        server_now = datetime.utcnow()
                        logger.info(f"🕐 Server UTC now: {server_now}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to parse scheduled_at '{scheduled_at}': {e}")
                        return error_response(f"Invalid scheduled_at format: {e}", "VALIDATION_ERROR", 400)
                else:
                    # Fallback to frequency-based scheduling
                    if freq == 'daily':
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=1)
                    elif freq == 'weekly':
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=7)
                    elif freq == 'monthly':
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=30)
                    elif freq == 'once':
                        # For one-time scheduling, we need the scheduled_at parameter
                        if not scheduled_at:
                            return error_response("scheduled_at parameter is required for one-time scheduling", "VALIDATION_ERROR", 400)
                    else:
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=7)  # Default to weekly
                
                # Schedule with Celery
                if aoi.next_run_at:
                    try:
                        from tasks import schedule_analysis_task
                        task_id = schedule_analysis_task(aoi_id, aoi.next_run_at)
                        logger.info(f"Scheduled Celery task {task_id} for AOI {aoi_id}")
                    except Exception as e:
                        logger.error(f"Failed to schedule Celery task: {e}")
                        # Continue anyway - the APScheduler fallback will handle it
                        
            # Log the changes we're about to commit
            logger.info(f"💾 About to commit AOI {aoi_id}: freq={aoi.monitoring_frequency}, next_run={aoi.next_run_at}, active={aoi.is_active}")
            
            session.commit()
            
            # Verify the commit worked
            session.refresh(aoi)
            logger.info(f"✅ After commit AOI {aoi_id}: freq={aoi.monitoring_frequency}, next_run={aoi.next_run_at}, active={aoi.is_active}")
            
            return success_response(
                data={
                    'aoi_id': aoi_id, 
                    'monitoring_frequency': aoi.monitoring_frequency,
                    'enabled': enabled,
                    'next_run_at': aoi.next_run_at.isoformat() if aoi.next_run_at else None,
                    'has_schedule': aoi.next_run_at is not None
                },
                message="Schedule updated successfully"
            )

        if request.method == 'DELETE':
            aoi.monitoring_frequency = None
            aoi.next_run_at = None
            aoi.is_active = True  # Keep AOI active, just remove schedule
            session.commit()
            
            return success_response(
                data={
                    'aoi_id': aoi_id, 
                    'monitoring_frequency': None
                },
                message="Schedule removed successfully"
            )

        return '', 204


@schedule_bp.route('/scheduler/status')
@require_auth
@handle_errors
def get_scheduler_status():
    """Get scheduler status and statistics"""
    try:
        # Get status from the main app's scheduler instead of creating a new one
        from flask import current_app
        if hasattr(current_app, 'auto_analysis_manager') and current_app.auto_analysis_manager:
            status = current_app.auto_analysis_manager.get_status()
        else:
            status = {'is_running': False, 'message': 'Scheduler not initialized'}
        
        # Get scheduled AOIs count
        with db_manager.get_session() as session:
            scheduled_aois = session.query(AreaOfInterest).filter(
                AreaOfInterest.monitoring_frequency.isnot(None),
                AreaOfInterest.is_active == True
            ).count()
        
        return success_response(
            data={
                'scheduler': status,
                'scheduled_aois': scheduled_aois,
                'message': '🤖 Scheduler running - checking hourly for due analyses' if status['is_running'] else '⚠️ Scheduler not running'
            },
            message="Scheduler status retrieved successfully"
        )
    except Exception as e:
        return error_response(f"Failed to get scheduler status: {str(e)}", "SCHEDULER_ERROR", 500)


@schedule_bp.route('/scheduler/trigger/<int:aoi_id>', methods=['POST'])
@require_auth
@handle_errors  
def trigger_analysis(aoi_id):
    """Manually trigger analysis for testing (admin/development)"""
    user_id = request.user['id']
    
    # Verify AOI ownership
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(id=aoi_id, user_id=user_id).first()
        if not aoi:
            return not_found_response("AOI not found")
    
    try:
        # Use the main app's scheduler instead of creating a new one
        from flask import current_app
        if hasattr(current_app, 'auto_analysis_manager') and current_app.auto_analysis_manager:
            success, message = current_app.auto_analysis_manager.force_analysis_for_aoi(aoi_id)
        else:
            return error_response("Scheduler not available", "SCHEDULER_NOT_AVAILABLE", 500)
        
        if success:
            return success_response(
                data={
                    'aoi_id': aoi_id
                },
                message=f"Manual analysis triggered for {aoi.name}"
            )
        else:
            return error_response(message, "ANALYSIS_TRIGGER_FAILED", 400)
            
    except Exception as e:
        return error_response(f"Failed to trigger analysis: {str(e)}", "ANALYSIS_TRIGGER_ERROR", 500)