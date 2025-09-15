"""
Image Controller
Handles image serving endpoints with S3 support
"""
import os
import logging
from flask import Blueprint, send_from_directory, abort, redirect, jsonify

# Import Config - if this fails, use fallback
try:
    from config import Config
    IMAGES_DIR = Config.IMAGES_DIR
except (ImportError, AttributeError) as e:
    logging.warning(f"Could not import Config.IMAGES_DIR: {e}, using fallback")
    IMAGES_DIR = 'images'

# Import S3 service
try:
    from services.s3_service import s3_service
    S3_ENABLED = True
except ImportError as e:
    logging.warning(f"S3 service not available: {e}")
    s3_service = None
    S3_ENABLED = False

logger = logging.getLogger(__name__)

# Create blueprint
image_bp = Blueprint('image', __name__, url_prefix='/api')


@image_bp.route('/image/<filename>')
def serve_image(filename):
    """Serve images from the images directory"""
    try:
        # Validate filename to prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Invalid filename requested: {filename}")
            abort(400)
        
        # Check if file exists
        
        file_path = os.path.join(IMAGES_DIR, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Image not found: {filename}")
            abort(404)
        
        logger.info(f"Serving image: {filename}")
        
        # Serve the file
        return send_from_directory(
            IMAGES_DIR, 
            filename,
            as_attachment=False,
            max_age=3600  # Cache for 1 hour
        )
        
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        abort(500)


@image_bp.route('/image/s3/<path:s3_key>')
def serve_s3_image(s3_key):
    """Generate signed URL for S3 image and redirect"""
    if not S3_ENABLED or not s3_service or not s3_service.enabled:
        logger.warning("S3 service not available for image serving")
        abort(503)  # Service unavailable
    
    try:
        # Generate signed URL (valid for 1 hour)
        signed_url = s3_service.generate_signed_url(s3_key, expiration=3600)
        
        if not signed_url:
            logger.warning(f"Could not generate signed URL for S3 key: {s3_key}")
            abort(404)
        
        # Redirect to the signed URL
        return redirect(signed_url)
        
    except Exception as e:
        logger.error(f"Error serving S3 image {s3_key}: {str(e)}")
        abort(500)


@image_bp.route('/image/upload-status')
def get_upload_status():
    """Get S3 upload configuration status"""
    return jsonify({
        's3_enabled': S3_ENABLED and s3_service and s3_service.enabled,
        'local_images_dir': IMAGES_DIR,
        'bucket_name': getattr(s3_service, 'bucket_name', None) if s3_service else None,
        'region': getattr(Config, 'AWS_S3_REGION', None)
    })


@image_bp.route('/image')
def list_images():
    """List all available images (for debugging) - local only"""
    try:
        if not os.path.exists(IMAGES_DIR):
            return {'images': [], 'count': 0, 's3_enabled': S3_ENABLED}
        
        images = []
        for filename in os.listdir(IMAGES_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                file_path = os.path.join(IMAGES_DIR, filename)
                file_size = os.path.getsize(file_path)
                images.append({
                    'filename': filename,
                    'size': file_size,
                    'url': f'/api/image/{filename}'
                })
        
        return {
            'images': images,
            'count': len(images),
            'images_dir': IMAGES_DIR,
            's3_enabled': S3_ENABLED and s3_service and s3_service.enabled
        }
        
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        return {'error': str(e)}, 500