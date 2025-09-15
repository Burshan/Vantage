# api/__init__.py - מנהל את כל ה-API routes

# ייבוא כל היצרנים של blueprints
from .auth import create_auth_blueprint
from .aoi import create_aoi_blueprint  
from .analysis import create_analysis_blueprint
from .system import create_system_blueprint

# אם יש צורך ב-admin routes
try:
    from .admin import create_admin_blueprint
except ImportError:
    # אם אין קובץ admin עדיין, ניצור blueprint ריק
    from flask import Blueprint
    def create_admin_blueprint(components):
        admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
        
        @admin_bp.route('/status')
        def admin_status():
            from flask import jsonify
            return jsonify({
                'message': 'Admin routes not implemented yet',
                'status': 'placeholder'
            })
        
        return admin_bp

__all__ = [
    'create_auth_blueprint',
    'create_aoi_blueprint', 
    'create_analysis_blueprint',
    'create_system_blueprint',
    'create_admin_blueprint'
]