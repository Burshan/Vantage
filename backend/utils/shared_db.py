"""
Shared Database Instance
Provides a single DatabaseManager instance for all controllers to prevent
multiple database connections and slow API performance.
"""
from database import DatabaseManager
from config import Config

# Single shared database instance
db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)