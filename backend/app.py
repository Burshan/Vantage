"""
Main Flask Application - Clean MVC Architecture
Satellite Intelligence System v2.0

This file is now the entry point for the application with proper separation of concerns:
- Controllers handle HTTP requests/responses
- Services handle business logic
- Models handle data
- Utils handle cross-cutting concerns
"""
import logging
import os
from datetime import datetime
from flask import Flask
from flask_cors import CORS

# Import configuration
from config import Config

# Import database and initialization
from database import DatabaseManager

# Import controllers (blueprints)
from controllers.user_controller import user_bp
from controllers.aoi_controller import aoi_bp
from controllers.analysis_controller import analysis_bp
from controllers.schedule_controller import schedule_bp
from controllers.admin_controller import admin_bp
from controllers.admin_token_controller import admin_token_bp
from controllers.baseline_controller import baseline_bp
from controllers.image_controller import image_bp

# Import middleware
from middleware.error_handlers import register_error_handlers

# Import auto-analysis manager
from auto_analysis import AutoAnalysisManager

# Import services
from services.satellite_service import SatelliteService
from services.satellite_service_opencv import SatelliteServiceOpenCV

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory pattern"""
    
    # Initialize Flask
    app = Flask(__name__)
    
    # Enable CORS with environment-based origins
    CORS(app, origins=Config.ALLOWED_ORIGINS)
    
    # Create directories
    os.makedirs(Config.IMAGES_DIR, exist_ok=True)
    
    # Initialize database manager
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    
    # Initialize satellite service (choose based on configuration)
    if Config.USE_OPENCV:
        satellite_service = SatelliteServiceOpenCV(Config.CLIENT_ID, Config.CLIENT_SECRET)
        logger.info("🔧 Using OpenCV-enhanced satellite service")
    else:
        satellite_service = SatelliteService(Config.CLIENT_ID, Config.CLIENT_SECRET)
        logger.info("🔧 Using matplotlib-based satellite service")
    
    # Store services in app context for access across the application
    app.db_manager = db_manager
    app.satellite_service = satellite_service
    
    # Register blueprints (controllers)
    app.register_blueprint(user_bp)
    app.register_blueprint(aoi_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_token_bp)
    app.register_blueprint(baseline_bp)
    app.register_blueprint(image_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize and start automatic analysis manager
    try:
        auto_analysis_manager = AutoAnalysisManager(db_manager, satellite_service)
        auto_analysis_manager.start()
        logger.info("🤖 Automatic Analysis Scheduler: STARTED")
        app.auto_analysis_manager = auto_analysis_manager
    except Exception as e:
        logger.warning(f"⚠️ Failed to start scheduler: {e}")
        app.auto_analysis_manager = None
    
    return app


def shutdown_app(app):
    """Clean shutdown of application services"""
    if hasattr(app, 'auto_analysis_manager') and app.auto_analysis_manager:
        try:
            app.auto_analysis_manager.stop()
            logger.info("🤖 Automatic Analysis Scheduler: STOPPED")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping scheduler: {e}")


# Create the application instance
app = create_app()


if __name__ == '__main__':
    logger.info(f"🌐 Server will run on http://{Config.API_HOST}:{Config.API_PORT}")
    
    try:
        app.run(
            host=Config.API_HOST, 
            port=Config.API_PORT, 
            debug=Config.DEBUG,
            threaded=True
        )
    finally:
        # Clean shutdown
        shutdown_app(app)
        