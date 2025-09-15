# app.py - מעודכן עם SQLAlchemy + Neon PostgreSQL (תוקן)
import matplotlib
matplotlib.use('Agg')
# app.py - עדכון endpoints לדשבורד AOI
import threading
import uuid
from datetime import datetime
import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO

import requests
import jwt
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
from sqlalchemy.sql import func

# Import our new modules
from config import Config
from database import DatabaseManager
from models import User, AreaOfInterest, AnalysisHistory, UserActivity
from auto_analysis import AutoAnalysisManager
from celery_app import celery_app

# פונקציה ליצירת baseline ברקע
def create_baseline_async(aoi_id: int):
    """Create baseline image asynchronously"""
    threading.Thread(
        target=lambda: db_manager.create_baseline_image(aoi_id, satellite_processor),
        daemon=True
    ).start()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Create directories
os.makedirs(Config.IMAGES_DIR, exist_ok=True)

# Initialize database manager
db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)

class ClerkAuthenticator:
    def __init__(self, clerk_secret_key):
        self.clerk_secret_key = clerk_secret_key
    
    def verify_token(self, token):
        """Verify Clerk JWT token"""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # In production, use proper signature verification
            options = {"verify_signature": False} if Config.DEBUG else {}
            
            decoded = jwt.decode(
                token,
                self.clerk_secret_key,
                algorithms=["RS256"],
                options=options
            )
            
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return None

# Initialize authenticator
clerk_auth = ClerkAuthenticator(Config.CLERK_SECRET_KEY)

def require_auth(f):
    """Enhanced authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'No authorization token provided',
                'code': 'NO_AUTH_HEADER'
            }), 401
        
        try:
            user_data = clerk_auth.verify_token(auth_header)
            if not user_data:
                return jsonify({
                    'error': 'Invalid or expired token',
                    'code': 'INVALID_TOKEN'
                }), 401
            
            logger.info(f"Auth successful for: {user_data.get('sub')}")
            
            # Get or create user in database
            user = db_manager.get_or_create_user(
                clerk_user_id=user_data.get('sub'),
                email=user_data.get('email'),
                first_name=user_data.get('given_name'),
                last_name=user_data.get('family_name')
            )
            
            logger.debug(f"Request user: {user}")
            request.user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 401
    
    return decorated_function

def handle_errors(f):
    """Global error handling decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'Invalid input',
                'message': str(e),
                'code': 'VALIDATION_ERROR'
            }), 400
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e) if Config.DEBUG else 'Something went wrong',
                'code': 'INTERNAL_ERROR'
            }), 500
    
    return decorated_function

class SatelliteProcessor:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://services.sentinel-hub.com"
        
    def get_access_token(self):
        """Get Sentinel Hub access token"""
        token_url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                logger.info("Successfully authenticated with Sentinel Hub")
                return True
            else:
                logger.error(f"Failed to get access token: {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Network error getting access token: {str(e)}")
            return False
    
    def download_image(self, bbox, date_from, date_to, width=1024, height=1024):
        """Download satellite image from Sentinel Hub"""
        if not self.access_token:
            if not self.get_access_token():
                return None
                
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04"]
                }],
                output: {
                    bands: 3,
                    sampleType: "AUTO"
                }
            };
        }

        function evaluatePixel(sample) {
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{date_from}T00:00:00Z",
                            "to": f"{date_to}T23:59:59Z"
                        },
                        "maxCloudCoverage": 20
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/jpeg"
                    }
                }]
            },
            "evalscript": evalscript
        }
        
        url = f"{self.base_url}/api/v1/process"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                logger.info(f"Downloaded image for {date_from} to {date_to}")
                return image
            else:
                logger.error(f"Error downloading image: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network error downloading image: {str(e)}")
            return None
    
    def create_heatmap(self, image1, image2, filename):
        """Create change detection heatmap"""
        try:
            img1_array = np.array(image1)
            img2_array = np.array(image2)
            
            if img1_array.shape != img2_array.shape:
                logger.error("Images have different sizes, cannot create heatmap")
                return None
            
            diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
            
            if len(diff.shape) == 3:
                diff_gray = np.mean(diff, axis=2)
            else:
                diff_gray = diff
            
            fig, ax = plt.subplots(1, 1, figsize=(12, 12), dpi=150)
            
            threshold = np.percentile(diff_gray, 75)
            enhanced_diff = np.where(diff_gray > threshold, diff_gray, 0)
            
            im = ax.imshow(enhanced_diff, cmap='hot', interpolation='bilinear')
            
            ax.set_title('Change Detection Heatmap', fontsize=18, fontweight='bold', pad=20)
            ax.axis('off')
            
            cbar = plt.colorbar(im, ax=ax, shrink=0.8, aspect=20)
            cbar.set_label('Change Intensity', rotation=270, labelpad=20, fontsize=12)
            
            plt.tight_layout()
            plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close()
            
            logger.info(f"Created heatmap: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {str(e)}")
            return None

# Initialize satellite processor
satellite_processor = SatelliteProcessor(Config.CLIENT_ID, Config.CLIENT_SECRET)

# Initialize automatic analysis manager
auto_analysis_manager = AutoAnalysisManager(db_manager, satellite_processor)

# ==================== API ENDPOINTS ====================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db_manager.get_session() as session:
            session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'service': 'satellite-intelligence-api',
            'version': '2.0.0',
            'environment': Config.ENVIRONMENT,
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/api/user/profile')
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
        return jsonify({'error': 'User not found'}), 404
    
    # Get recent history
    history = db_manager.get_user_history(user_id, limit=5)
    
    logger.info(f"Sending profile response: tokens_remaining={fresh_user['tokens_remaining']}")
    
    return jsonify({
        'success': True,
        'user': {
            'id': fresh_user['id'],
            'email': fresh_user['email'],
            'first_name': fresh_user['first_name'],
            'last_name': fresh_user['last_name'],
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
    })

@app.route('/api/debug/user-status')
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
    
    return jsonify({
        'debug_info': {
            'request_user': user_dict,
            'db_user': user.to_dict() if user else None,
            'aoi_count': aoi_count,
            'analysis_count': analysis_count,
            'recent_activity': [activity.to_dict() for activity in recent_activity],
            'database_url': Config.DATABASE_URL.split('@')[0] + '@[HIDDEN]',
            'timestamp': datetime.now().isoformat()
        }
    })

@app.route('/api/aoi', methods=['GET'])
@require_auth
@handle_errors
def get_aois():
    """Get user's Areas of Interest with dashboard info"""
    user_id = request.user['id']
    aois = db_manager.get_user_aois(user_id)
    
    return jsonify({
        'success': True,
        'areas_of_interest': aois,
        'total_count': len(aois)
    })


@app.route('/api/aoi', methods=['POST'])
@require_auth
@handle_errors
def create_aoi():
    """Create a new Area of Interest with automatic baseline creation"""
    user_id = request.user['id']
    aoi_data = request.get_json()
    
    logger.info(f"Create AOI request from user {user_id}")
    logger.debug(f"Request data: {aoi_data}")
    
    # Validate required fields
    if not aoi_data.get('name'):
        raise ValueError('AOI name is required')
    
    bbox_coords = aoi_data.get('bbox_coordinates')
    if not bbox_coords or not isinstance(bbox_coords, list) or len(bbox_coords) != 4:
        raise ValueError('Valid bbox coordinates are required: [lat_min, lon_min, lat_max, lon_max]')

    lat_min, lon_min, lat_max, lon_max = bbox_coords

    # Validation
    if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
        raise ValueError('Latitude values must be between -90 and 90')
    if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
        raise ValueError('Longitude values must be between -180 and 180')
    if lat_min >= lat_max or lon_min >= lon_max:
        raise ValueError('Invalid bounding box: min values must be less than max values')

    # Convert to Sentinel order before saving
    aoi_data['bbox_coordinates'] = [lon_min, lat_min, lon_max, lat_max]
    
    logger.info("Validation passed, creating AOI...")
    
    # Create AOI
    aoi_id = db_manager.create_aoi(user_id, aoi_data)
    
    # Start baseline creation in background
    create_baseline_async(aoi_id)
    
    logger.info(f"AOI created successfully with ID: {aoi_id}")
    
    return jsonify({
        'success': True,
        'aoi_id': aoi_id,
        'message': 'AOI created successfully. Baseline image creation started.',
        'baseline_status': 'pending'
    })

@app.route('/api/aoi/<int:aoi_id>', methods=['DELETE'])
@require_auth
@handle_errors
def delete_aoi(aoi_id):
    """Delete an Area of Interest"""
    user_id = request.user['id']
    success, message = db_manager.delete_aoi(user_id, aoi_id)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 404

@app.route('/api/user/history')
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
    
    return jsonify({
        'success': True,
        'history': history,
        'total_analyses': len(history)
    })

@app.route('/api/process-satellite-images', methods=['POST'])
@require_auth
@handle_errors
def process_satellite_images():
    """Process satellite images - for manual analysis without AOI"""
    user_dict = request.user
    user_id = user_dict['id']
    data = request.get_json() or {}
    
    # Check if user has tokens
    if user_dict['tokens_remaining'] <= 0:
        return jsonify({
            'error': 'No tokens remaining',
            'tokens_remaining': 0,
            'message': 'Contact administrator to purchase more tokens'
        }), 402
    
    logger.info(f"Starting manual satellite analysis for user: {user_dict.get('email', user_id)}")
    
    # Use a token
    success, message = db_manager.use_token(user_id)
    if not success:
        return jsonify({'error': message}), 402
    
    # Get updated user data
    updated_user = db_manager.get_user_by_id(user_id)
    
    # Default coordinates for manual analysis
    bbox = data.get('bbox_coordinates', [50.964594, 34.876149, 51.025335, 34.911741])
    location_description = data.get('location_description', "Manual Analysis")
    
    # Date ranges for comparison
    date1_from = data.get('date1_from', "2021-08-01")
    date1_to = data.get('date1_to', "2021-08-31")
    date2_from = data.get('date2_from', "2025-08-01")
    date2_to = data.get('date2_to', "2025-08-31")
    
    process_id = str(uuid.uuid4())[:8]
    
    # Download images
    image1 = satellite_processor.download_image(bbox, date1_from, date1_to)
    if not image1:
        return jsonify({'error': 'Failed to download first image'}), 500
    
    image2 = satellite_processor.download_image(bbox, date2_from, date2_to)
    if not image2:
        return jsonify({'error': 'Failed to download second image'}), 500
    
    # Create filenames
    image1_filename = f"manual_{user_id}_image1_{process_id}.jpg"
    image2_filename = f"manual_{user_id}_image2_{process_id}.jpg"
    heatmap_filename = f"manual_{user_id}_heatmap_{process_id}.png"
    
    image1_path = os.path.join(Config.IMAGES_DIR, image1_filename)
    image2_path = os.path.join(Config.IMAGES_DIR, image2_filename)
    heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
    
    # Save images
    image1.save(image1_path, 'JPEG', quality=95)
    image2.save(image2_path, 'JPEG', quality=95)
    
    # Create heatmap
    satellite_processor.create_heatmap(image1, image2, heatmap_path)
    
    # Calculate change percentage
    import numpy as np
    img1_array = np.array(image1)
    img2_array = np.array(image2)
    diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
    change_percentage = (np.mean(diff) / 255.0) * 100
    
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
        meta={
            'date1_from': date1_from,
            'date1_to': date1_to,
            'date2_from': date2_from,
            'date2_to': date2_to,
            'processing_time': datetime.now().isoformat()
        },
        change_percentage=change_percentage,
        tokens_used=1
    )
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'process_id': process_id,
        'change_percentage': round(change_percentage, 2),
        'message': 'Images processed successfully',
        'user_tokens': {
            'tokens_remaining': updated_user['tokens_remaining'],
            'tokens_used_this_session': 1
        },
        'images': {
            'image1': {
                'filename': image1_filename,
                'url': f'/api/image/{image1_filename}',
                'period': f"{date1_from} to {date1_to}",
                'description': 'Historical Satellite Image'
            },
            'image2': {
                'filename': image2_filename, 
                'url': f'/api/image/{image2_filename}',
                'period': f"{date2_from} to {date2_to}",
                'description': 'Current Satellite Image'
            },
            'heatmap': {
                'filename': heatmap_filename,
                'url': f'/api/image/{heatmap_filename}',
                'description': 'Change Detection Heatmap'
            }
        }
    })
    
@app.route('/api/image/<filename>')
@handle_errors
def get_image(filename):
    """Serve image files with security checks"""
    # Basic security: only allow alphanumeric, underscore, dash, and dot
    import re
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(Config.IMAGES_DIR, filename)
    
    # Security: ensure the file is within the images directory
    if not os.path.abspath(filepath).startswith(os.path.abspath(Config.IMAGES_DIR)):
        return jsonify({'error': 'Access denied'}), 403
    
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/admin/stats')
@require_auth
@handle_errors
def get_admin_stats():
    """Get system statistics"""
    user_id = request.user['id']
    
    with db_manager.get_session() as session:
        # Get comprehensive statistics
        total_users = session.query(User).count()
        total_analyses = session.query(AnalysisHistory).count()
        total_tokens_used = session.query(func.sum(User.total_tokens_used)).scalar() or 0
        active_aois = session.query(AreaOfInterest).filter_by(is_active=True).count()
        
        # Recent activity
        recent_activity = session.query(UserActivity).join(User).filter(
            UserActivity.timestamp >= datetime.now() - timedelta(days=7)
        ).order_by(UserActivity.timestamp.desc()).limit(10).all()
        
        # User-specific stats
        user_aois = session.query(AreaOfInterest).filter_by(
            user_id=user_id, is_active=True
        ).count()
        user_analyses = session.query(AnalysisHistory).filter_by(
            user_id=user_id
        ).count()
    
    return jsonify({
        'success': True,
        'system_stats': {
            'total_users': total_users,
            'total_analyses': total_analyses,
            'total_tokens_used': total_tokens_used,
            'active_aois': active_aois
        },
        'user_stats': {
            'user_aois': user_aois,
            'user_analyses': user_analyses
        },
        'recent_activity': [
            {
                'activity_type': activity.activity_type,
                'timestamp': activity.timestamp.isoformat(),
                'user_email': activity.user.email if activity.user else None
            } for activity in recent_activity
        ]
    })


@app.route('/api/aoi/<int:aoi_id>/history')
@require_auth
@handle_errors
def get_aoi_history(aoi_id):
    """Get analysis history for specific AOI"""
    user_id = request.user['id']
    limit = request.args.get('limit', 20, type=int)
    
    with db_manager.get_session() as session:
        # Verify access
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404
        
        # Get analysis history
        analyses = session.query(AnalysisHistory).filter_by(
            aoi_id=aoi_id
        ).order_by(AnalysisHistory.analysis_timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'success': True,
        'aoi_id': aoi_id,
        'aoi_name': aoi.name,
        'analyses': [analysis.to_dict() for analysis in analyses],
        'total_count': len(analyses)
    })

@app.route('/api/aoi/<int:aoi_id>/dashboard', methods=['GET'])
@require_auth
@handle_errors
def get_aoi_dashboard_view(aoi_id):
    """Get AOI dashboard for viewing only - no analysis execution"""
    user_id = request.user['id']
    
    logger.info(f"Getting dashboard view for AOI {aoi_id}, user {user_id}")
    
    with db_manager.get_session() as session:
        # Get AOI details
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404
        
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
                        'image1_url': f'/api/image/{analysis.image1_filename}' if analysis.image1_filename else None,
                        'image2_url': f'/api/image/{analysis.image2_filename}' if analysis.image2_filename else None,
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
    
    return jsonify({
        'success': True,
        'dashboard': dashboard_data
    })


@app.route('/api/aoi/<int:aoi_id>/run-analysis', methods=['POST'])
@require_auth
@handle_errors  
def run_aoi_analysis_manual(aoi_id):
    """Manually trigger analysis for AOI (separate from dashboard view)"""
    user_dict = request.user
    user_id = user_dict['id']
    
    logger.info(f"Manual analysis triggered for AOI {aoi_id} by user {user_id}")
    
    # Check if user has tokens
    if user_dict['tokens_remaining'] <= 0:
        return jsonify({
            'error': 'No tokens remaining',
            'tokens_remaining': 0,
            'message': 'Contact administrator to purchase more tokens'
        }), 402
    
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404
        
        if aoi.baseline_status != 'completed':
            return jsonify({
                'error': 'Baseline image not ready',
                'baseline_status': aoi.baseline_status,
                'message': 'Please wait for baseline creation to complete before running analysis'
            }), 400
    
    # Use a token
    success, message = db_manager.use_token(user_id)
    if not success:
        return jsonify({'error': message}), 402
    
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
    # Fresh session to fetch AOI
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404
        
        # Get current date for new image
        current_date = datetime.now()
        date_from = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = current_date.strftime("%Y-%m-%d")
        
        process_id = str(uuid.uuid4())[:8]
        
        # Download current image
        current_image = satellite_processor.download_image(
            bbox=aoi.bbox_coordinates,
            date_from=date_from,
            date_to=date_to
        )
        
        if not current_image:
            return jsonify({'error': 'Failed to download current image'}), 500
        
        # Load baseline image
        baseline_path = os.path.join(Config.IMAGES_DIR, aoi.baseline_image_filename)
        if not os.path.exists(baseline_path):
            return jsonify({'error': 'Baseline image not found'}), 500
        
        from PIL import Image
        baseline_image = Image.open(baseline_path)
        
        # Create filenames
        current_filename = f"aoi_{aoi.id}_current_{process_id}.jpg"
        heatmap_filename = f"aoi_{aoi.id}_heatmap_{process_id}.png"
        
        current_path = os.path.join(Config.IMAGES_DIR, current_filename)
        heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
        
        # Save current image
        current_image.save(current_path, 'JPEG', quality=95)
        
        # Create heatmap
        satellite_processor.create_heatmap(baseline_image, current_image, heatmap_path)
        
        # Calculate change percentage
        import numpy as np
        baseline_array = np.array(baseline_image)
        current_array = np.array(current_image)
        diff = np.abs(baseline_array.astype(float) - current_array.astype(float))
        change_percentage = (np.mean(diff) / 255.0) * 100
        
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
            meta={
                'analysis_date': current_date.isoformat(),
                'comparison_type': 'baseline_vs_current',
                'analysis_type': 'manual_trigger'
            },
            change_percentage=change_percentage,
            tokens_used=1
        )
        
        # Get updated user data
        updated_user = db_manager.get_user_by_id(user_id)
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'process_id': process_id,
            'change_percentage': round(change_percentage, 2),
            'message': 'Analysis completed successfully',
            'user_tokens': {
                'tokens_remaining': updated_user['tokens_remaining'],
                'tokens_used_this_session': 1
            },
            'images': {
                'baseline': {
                    'filename': aoi.baseline_image_filename,
                    'url': f'/api/image/{aoi.baseline_image_filename}',
                    'description': 'Baseline Image'
                },
                'current': {
                    'filename': current_filename,
                    'url': f'/api/image/{current_filename}',
                    'description': 'Current Analysis Image'
                },
                'heatmap': {
                    'filename': heatmap_filename,
                    'url': f'/api/image/{heatmap_filename}',
                    'description': 'Change Detection Heatmap'
                }
            }
        })


def _run_time_range_analysis(aoi_id, user_id, request_data):
    """Run analysis between two time ranges"""
    # Fresh session to fetch AOI
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(
            id=aoi_id, 
            user_id=user_id
        ).first()
        
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404
        
        # Get date ranges from request
        date1_from = request_data.get('date1_from')
        date1_to = request_data.get('date1_to')
        date2_from = request_data.get('date2_from')
        date2_to = request_data.get('date2_to')
        
        if not all([date1_from, date1_to, date2_from, date2_to]):
            return jsonify({'error': 'All date ranges are required for time range analysis'}), 400
        
        process_id = str(uuid.uuid4())[:8]
        
        # Download both images
        image1 = satellite_processor.download_image(aoi.bbox_coordinates, date1_from, date1_to)
        image2 = satellite_processor.download_image(aoi.bbox_coordinates, date2_from, date2_to)
        
        if not image1 or not image2:
            return jsonify({'error': 'Failed to download one or both images'}), 500
        
        # Create filenames
        image1_filename = f"aoi_{aoi.id}_period1_{process_id}.jpg"
        image2_filename = f"aoi_{aoi.id}_period2_{process_id}.jpg"
        heatmap_filename = f"aoi_{aoi.id}_comparison_{process_id}.png"
        
        image1_path = os.path.join(Config.IMAGES_DIR, image1_filename)
        image2_path = os.path.join(Config.IMAGES_DIR, image2_filename)
        heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
        
        # Save images
        image1.save(image1_path, 'JPEG', quality=95)
        image2.save(image2_path, 'JPEG', quality=95)
        
        # Create heatmap
        satellite_processor.create_heatmap(image1, image2, heatmap_path)
        
        # Calculate change percentage
        import numpy as np
        img1_array = np.array(image1)
        img2_array = np.array(image2)
        diff = np.abs(img1_array.astype(float) - img2_array.astype(float))
        change_percentage = (np.mean(diff) / 255.0) * 100
        
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
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'process_id': process_id,
            'change_percentage': round(change_percentage, 2),
            'message': 'Time range analysis completed successfully',
            'user_tokens': {
                'tokens_remaining': updated_user['tokens_remaining'],
                'tokens_used_this_session': 1
            },
            'images': {
                'period1': {
                    'filename': image1_filename,
                    'url': f'/api/image/{image1_filename}',
                    'description': f'Period 1: {date1_from} to {date1_to}'
                },
                'period2': {
                    'filename': image2_filename,
                    'url': f'/api/image/{image2_filename}',
                    'description': f'Period 2: {date2_from} to {date2_to}'
                },
                'heatmap': {
                    'filename': heatmap_filename,
                    'url': f'/api/image/{heatmap_filename}',
                    'description': 'Change Detection Heatmap'
                }
            }
        })

# @app.route('/api/aoi/<int:aoi_id>/analysis', methods=['POST'])
# @require_auth
# @handle_errors
# def run_manual_analysis(aoi_id):
#     """Run manual analysis for AOI (compare with baseline or last image)"""
#     user_dict = request.user
#     user_id = user_dict['id']
    
#     # Check if user has tokens
#     if user_dict['tokens_remaining'] <= 0:
#         return jsonify({
#             'error': 'No tokens remaining',
#             'tokens_remaining': 0,
#             'message': 'Contact administrator to purchase more tokens'
#         }), 402
    
#     with db_manager.get_session() as session:
#         aoi = session.query(AreaOfInterest).filter_by(
#             id=aoi_id, 
#             user_id=user_id
#         ).first()
        
#         if not aoi:
#             return jsonify({'error': 'AOI not found'}), 404
        
#         if aoi.baseline_status != 'completed':
#             return jsonify({
#                 'error': 'Baseline image not ready',
#                 'baseline_status': aoi.baseline_status
#             }), 400
    
#     # Use a token
#     success, message = db_manager.use_token(user_id)
#     if not success:
#         return jsonify({'error': message}), 402
    
#     logger.info(f"Starting manual analysis for AOI {aoi_id}")
    
#     # Get current date for new image
#     current_date = datetime.now()
#     date_from = (current_date - timedelta(days=7)).strftime("%Y-%m-%d")
#     date_to = current_date.strftime("%Y-%m-%d")
    
#     process_id = str(uuid.uuid4())[:8]
    
#     # Download current image
#     current_image = satellite_processor.download_image(
#         bbox=aoi.bbox_coordinates,
#         date_from=date_from,
#         date_to=date_to
#     )
    
#     if not current_image:
#         return jsonify({'error': 'Failed to download current image'}), 500
    
#     # Load baseline image
#     baseline_path = os.path.join(Config.IMAGES_DIR, aoi.baseline_image_filename)
#     if not os.path.exists(baseline_path):
#         return jsonify({'error': 'Baseline image not found'}), 500
    
#     from PIL import Image
#     baseline_image = Image.open(baseline_path)
    
#     # Create filenames
#     current_filename = f"aoi_{aoi_id}_current_{process_id}.jpg"
#     heatmap_filename = f"aoi_{aoi_id}_heatmap_{process_id}.png"
    
#     current_path = os.path.join(Config.IMAGES_DIR, current_filename)
#     heatmap_path = os.path.join(Config.IMAGES_DIR, heatmap_filename)
    
#     # Save current image
#     current_image.save(current_path, 'JPEG', quality=95)
    
#     # Create heatmap
#     satellite_processor.create_heatmap(baseline_image, current_image, heatmap_path)
    
#     # Calculate change percentage (simple implementation)
#     import numpy as np
#     baseline_array = np.array(baseline_image)
#     current_array = np.array(current_image)
#     diff = np.abs(baseline_array.astype(float) - current_array.astype(float))
#     change_percentage = (np.mean(diff) / 255.0) * 100
    
#     # Save to database
#     analysis_id = db_manager.save_analysis(
#         user_id=user_id,
#         aoi_id=aoi_id,
#         process_id=process_id,
#         operation_name="MANUAL ANALYSIS",
#         location_description=f"{aoi.name} - {aoi.location_name}",
#         bbox_coordinates=aoi.bbox_coordinates,
#         image_filenames={
#             'image1': aoi.baseline_image_filename,  # baseline
#             'image2': current_filename,             # current
#             'heatmap': heatmap_filename
#         },
#         meta={
#             'analysis_date': current_date.isoformat(),
#             'comparison_type': 'baseline_vs_current',
#             'processing_time': datetime.now().isoformat()
#         },
#         tokens_used=1
#     )
    
#     # Get updated user data
#     updated_user = db_manager.get_user_by_id(user_id)
    
#     return jsonify({
#         'success': True,
#         'analysis_id': analysis_id,
#         'process_id': process_id,
#         'user_tokens': {
#             'tokens_remaining': updated_user['tokens_remaining'],
#             'tokens_used_this_session': 1
#         },
#         'images': {
#             'baseline': {
#                 'filename': aoi.baseline_image_filename,
#                 'url': f'/api/image/{aoi.baseline_image_filename}',
#                 'description': 'Baseline Image'
#             },
#             'current': {
#                 'filename': current_filename,
#                 'url': f'/api/image/{current_filename}',
#                 'description': 'Current Analysis Image'
#             },
#             'heatmap': {
#                 'filename': heatmap_filename,
#                 'url': f'/api/image/{heatmap_filename}',
#                 'description': 'Change Detection Heatmap'
#             }
#         }
#     })


@app.route('/api/aoi/<int:aoi_id>/baseline', methods=['POST'])
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
            return jsonify({'error': 'AOI not found'}), 404
        
        if aoi.baseline_status == 'processing':
            return jsonify({'error': 'Baseline creation already in progress'}), 400
    
    # Start baseline creation
    create_baseline_async(aoi_id)
    
    return jsonify({
        'success': True,
        'message': 'Baseline creation started',
        'aoi_id': aoi_id
    })

@app.route('/api/aoi/<int:aoi_id>/baseline', methods=['GET'])
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
            return jsonify({'error': 'AOI not found'}), 404
    
    return jsonify({
        'aoi_id': aoi_id,
        'baseline_status': aoi.baseline_status,
        'baseline_date': aoi.baseline_date.isoformat() if aoi.baseline_date else None,
        'baseline_image_url': f'/api/image/{aoi.baseline_image_filename}' if aoi.baseline_image_filename else None
    })

@app.route('/api/aoi/<int:aoi_id>', methods=['GET'])
@require_auth
@handle_errors
def get_aoi_dashboard(aoi_id):
    """Get comprehensive AOI dashboard"""
    user_id = request.user['id']
    
    dashboard_data = db_manager.get_aoi_dashboard(aoi_id, user_id)
    if not dashboard_data:
        return jsonify({'error': 'AOI not found or access denied'}), 404
    
    return jsonify({
        'success': True,
        'dashboard': dashboard_data
    })

@app.route('/api/debug/ping')
def debug_ping():
    return jsonify({
        'success': True, 
        'message': 'Backend is responding',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/aoi/<int:aoi_id>/schedule-monitoring', methods=['GET','POST','DELETE','OPTIONS'])
@require_auth
@handle_errors
def schedule_monitoring(aoi_id):
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
    # וידוא גישה
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(id=aoi_id, user_id=user_id).first()
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404

        if request.method == 'GET':
            return jsonify({
                'success': True,
                'aoi_id': aoi_id,
                'monitoring_frequency': aoi.monitoring_frequency,
                'next_run_at': aoi.next_run_at.isoformat() if getattr(aoi, 'next_run_at', None) else None,
                'is_active': aoi.is_active,
                'has_schedule': aoi.next_run_at is not None
            })

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
                return jsonify({'error': 'frequency parameter is required when enabling schedule'}), 400

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
                    from datetime import datetime
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
                        return jsonify({'error': f'Invalid scheduled_at format: {e}'}), 400
                else:
                    # Fallback to frequency-based scheduling
                    from datetime import datetime, timedelta
                    if freq == 'daily':
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=1)
                    elif freq == 'weekly':
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=7)
                    elif freq == 'monthly':
                        aoi.next_run_at = datetime.utcnow() + timedelta(days=30)
                    elif freq == 'once':
                        # For one-time scheduling, we need the scheduled_at parameter
                        if not scheduled_at:
                            return jsonify({'error': 'scheduled_at parameter is required for one-time scheduling'}), 400
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
            
            return jsonify({
                'success': True, 
                'aoi_id': aoi_id, 
                'monitoring_frequency': aoi.monitoring_frequency,
                'enabled': enabled,
                'next_run_at': aoi.next_run_at.isoformat() if aoi.next_run_at else None,
                'has_schedule': aoi.next_run_at is not None,
                'message': 'Schedule updated successfully'
            })

        if request.method == 'DELETE':
            aoi.monitoring_frequency = None
            aoi.next_run_at = None
            aoi.is_active = True  # Keep AOI active, just remove schedule
            session.commit()
            return jsonify({
                'success': True, 
                'aoi_id': aoi_id, 
                'monitoring_frequency': None,
                'message': 'Schedule removed successfully'
            })

        return '', 204

@app.route('/api/scheduler/status')
@require_auth
@handle_errors
def get_scheduler_status():
    """Get scheduler status and statistics"""
    try:
        status = auto_analysis_manager.get_status()
        
        # Get scheduled AOIs count
        with db_manager.get_session() as session:
            scheduled_aois = session.query(AreaOfInterest).filter(
                AreaOfInterest.monitoring_frequency.isnot(None),
                AreaOfInterest.is_active == True
            ).count()
        
        return jsonify({
            'success': True,
            'scheduler': status,
            'scheduled_aois': scheduled_aois,
            'message': '🤖 Scheduler running - checking hourly for due analyses' if status['is_running'] else '⚠️ Scheduler not running'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get scheduler status: {str(e)}'
        }), 500

@app.route('/api/scheduler/trigger/<int:aoi_id>', methods=['POST'])
@require_auth
@handle_errors  
def trigger_analysis(aoi_id):
    """Manually trigger analysis for testing (admin/development)"""
    user_id = request.user['id']
    
    # Verify AOI ownership
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(id=aoi_id, user_id=user_id).first()
        if not aoi:
            return jsonify({'error': 'AOI not found'}), 404
    
    try:
        success, message = auto_analysis_manager.force_analysis_for_aoi(aoi_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Manual analysis triggered for {aoi.name}',
                'aoi_id': aoi_id
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to trigger analysis: {str(e)}'
        }), 500




# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    logger.info("🛰️ Starting Satellite Intelligence System v2.0")
    logger.info("🔐 Clerk Authentication: ENABLED")
    logger.info(f"🗄️ Database: {Config.DATABASE_URL.split('@')[0]}@[HIDDEN]")
    logger.info("💳 Token System: ACTIVE")
    logger.info("📍 AOI Management: ENABLED")
    logger.info(f"🌐 Environment: {Config.ENVIRONMENT}")
    
    # Start automatic analysis scheduler
    try:
        auto_analysis_manager.start()
        logger.info("🤖 Automatic Analysis Scheduler: STARTED")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start scheduler: {e}")
    
    logger.info("🌐 Server will run on http://localhost:5000")
    
    try:
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=Config.DEBUG,
            threaded=True
        )
    finally:
        # Stop scheduler on shutdown
        try:
            auto_analysis_manager.stop()
            logger.info("🤖 Automatic Analysis Scheduler: STOPPED")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping scheduler: {e}")