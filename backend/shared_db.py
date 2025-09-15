"""
Shared Database Manager Instance
===============================

This module provides a global database manager instance that can be imported
across the application. It's initialized once and reused everywhere.

This is needed for the current controller architecture where controllers
import db_manager directly rather than receiving it as a dependency.
"""

from database import DatabaseManager
from config import Config

# Create a global database manager instance
# This will be initialized when the module is first imported
db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)