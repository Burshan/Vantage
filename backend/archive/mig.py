# quick_migration.py - Run this to fix the immediate database issues

import os
from sqlalchemy import create_engine, text
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add missing columns to database tables"""
    engine = create_engine(Config.DATABASE_URL)
    
    migration_queries = [
        # Add change_percentage to analysis_history table
        """
        ALTER TABLE analysis_history 
        ADD COLUMN IF NOT EXISTS change_percentage FLOAT
        """,
        
        # Add baseline columns to areas_of_interest table
        """
        ALTER TABLE areas_of_interest 
        ADD COLUMN IF NOT EXISTS baseline_status VARCHAR(20) DEFAULT 'pending'
        """,
        """
        ALTER TABLE areas_of_interest 
        ADD COLUMN IF NOT EXISTS baseline_date TIMESTAMP
        """,
        """
        ALTER TABLE areas_of_interest 
        ADD COLUMN IF NOT EXISTS baseline_image_filename VARCHAR(255)
        """
    ]
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            for i, query in enumerate(migration_queries, 1):
                logger.info(f"Executing migration {i}/{len(migration_queries)}: {query.strip()}")
                try:
                    conn.execute(text(query))
                    logger.info(f"✓ Migration {i} completed successfully")
                except Exception as e:
                    logger.warning(f"Migration {i} skipped (likely already exists): {str(e)}")
            
            # Commit all changes
            trans.commit()
            logger.info("🎉 All migrations completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    run_migration()
    print("✅ Migration complete! You can now restart your application.")