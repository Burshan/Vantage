#!/usr/bin/env python3
"""
Database migration: Add next_run_at column to areas_of_interest table
"""

import logging
from sqlalchemy import create_engine, text
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add next_run_at column to areas_of_interest table"""
    
    engine = create_engine(Config.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'areas_of_interest' 
                AND column_name = 'next_run_at'
            """))
            
            if result.fetchone():
                logger.info("✅ Column 'next_run_at' already exists")
                return
            
            # Add the column
            logger.info("🔄 Adding 'next_run_at' column to areas_of_interest table...")
            
            conn.execute(text("""
                ALTER TABLE areas_of_interest 
                ADD COLUMN next_run_at TIMESTAMP NULL
            """))
            
            # Create index for performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_areas_of_interest_next_run_at 
                ON areas_of_interest(next_run_at)
            """))
            
            conn.commit()
            logger.info("✅ Successfully added 'next_run_at' column and index")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == '__main__':
    logger.info("🔧 Starting database migration...")
    run_migration()
    logger.info("🎉 Migration completed!")