#!/usr/bin/env python3
"""
Database migration to add S3 columns to analysis_history table
"""
import logging
from sqlalchemy import text
from shared_db import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_s3_columns():
    """Add S3 key columns to analysis_history table"""
    
    # SQL to add the new columns
    migration_sql = """
    ALTER TABLE analysis_history 
    ADD COLUMN IF NOT EXISTS image1_s3_key VARCHAR(512),
    ADD COLUMN IF NOT EXISTS image2_s3_key VARCHAR(512),
    ADD COLUMN IF NOT EXISTS heatmap_s3_key VARCHAR(512);
    """
    
    try:
        with db_manager.get_session() as session:
            logger.info("Starting S3 columns migration...")
            
            # Execute the migration
            session.execute(text(migration_sql))
            session.commit()
            
            logger.info("✅ Successfully added S3 columns to analysis_history table")
            
            # Verify the columns were added
            verify_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'analysis_history' 
            AND column_name IN ('image1_s3_key', 'image2_s3_key', 'heatmap_s3_key');
            """
            
            result = session.execute(text(verify_sql))
            columns = [row[0] for row in result]
            
            logger.info(f"✅ Verified columns exist: {columns}")
            
            if len(columns) == 3:
                logger.info("🎉 Migration completed successfully!")
                return True
            else:
                logger.error(f"❌ Expected 3 columns, but found {len(columns)}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔄 Running S3 columns migration...")
    success = migrate_s3_columns()
    
    if success:
        print("✅ Migration completed! You can now restart your server.")
    else:
        print("❌ Migration failed. Check the logs above.")