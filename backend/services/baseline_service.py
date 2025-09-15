"""
Baseline Service
Handles baseline image creation and management
"""
import threading
import logging
from database import DatabaseManager
from config import Config

logger = logging.getLogger(__name__)

# Initialize database manager
db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)


def create_baseline_async(aoi_id: int):
    """Create baseline image asynchronously"""
    threading.Thread(
        target=lambda: _create_baseline_image(aoi_id),
        daemon=True
    ).start()


def _create_baseline_image(aoi_id: int):
    """Create baseline image for AOI"""
    try:
        # Import here to avoid circular imports
        from services.satellite_service import SatelliteService
        
        satellite_processor = SatelliteService(Config.CLIENT_ID, Config.CLIENT_SECRET)
        return db_manager.create_baseline_image(aoi_id, satellite_processor)
    except Exception as e:
        logger.error(f"Error creating baseline image for AOI {aoi_id}: {e}")
        return False