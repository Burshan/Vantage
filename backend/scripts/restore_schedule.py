#!/usr/bin/env python3
"""
Restore the original schedule time
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from config import Config
from models import AreaOfInterest

def restore_original_schedule():
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    
    with db_manager.get_session() as session:
        aoi = session.query(AreaOfInterest).filter_by(id=14).first()
        
        if aoi:
            # Restore the time that was showing before (12:46)
            restore_time = datetime(2025, 9, 8, 12, 46, 0)
            aoi.monitoring_frequency = 'once'
            aoi.next_run_at = restore_time
            aoi.is_active = True
            
            session.commit()
            print(f"✅ Restored schedule to: {restore_time}")
        else:
            print("❌ AOI 14 not found")

if __name__ == '__main__':
    restore_original_schedule()