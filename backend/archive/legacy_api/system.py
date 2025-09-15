# api/system.py - API routes עבור מידע מערכת ובדיקות בריאות
from datetime import datetime
from flask import Blueprint, jsonify

def create_system_blueprint(components):
    """יוצר Blueprint עבור API routes של מערכת"""
    
    system_bp = Blueprint('system', __name__, url_prefix='/api')
    
    # קבלת הקומפוננטים
    auto_analysis_manager = components['auto_analysis_manager']
    
    @system_bp.route('/health')
    def health():
        """בדיקת תקינות המערכת"""
        return jsonify({
            'status': 'healthy',
            'service': 'vantage-satellite-intelligence',
            'version': '3.0',
            'components': {
                'database': 'OK',
                'auth': 'OK',
                'satellite_processor': 'OK',
                'auto_analysis': auto_analysis_manager.get_status()
            },
            'timestamp': datetime.now().isoformat()
        })

    @system_bp.route('/system/info')
    def get_system_info():
        """מידע כללי על המערכת (נקודת קצה ציבורית)"""
        return jsonify({
            'service': 'VANTAGE Satellite Intelligence System',
            'version': '3.0',
            'database': 'SQLite Enhanced',
            'features': [
                'Clerk Authentication',
                'Token-based Usage System',
                'Areas of Interest Management',
                'Custom Refresh Intervals',
                'Automatic Analysis Scheduling',
                'Change Detection & Heatmaps',
                'User Activity Tracking',
                'Hebrew/English Support',
                'Real-time Satellite Processing'
            ],
            'endpoints': {
                'health': '/api/health',
                'user_profile': '/api/user/profile',
                'aoi_management': '/api/aoi',
                'satellite_processing': '/api/process-satellite-images',
                'image_serving': '/api/image/<filename>'
            },
            'status': 'operational',
            'timestamp': datetime.now().isoformat()
        })
    
    return system_bp