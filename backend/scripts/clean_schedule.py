#!/usr/bin/env python3
"""
Clean up the problematic schedule for AOI 14
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from config import Config
from models import AreaOfInterest

def clean_aoi_schedule():
    """Clean up AOI 14 schedule"""
    print("🧹 Cleaning AOI 14 Schedule")
    print("=" * 50)
    
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    
    try:
        with db_manager.get_session() as session:
            # Get AOI 14
            aoi = session.query(AreaOfInterest).filter_by(id=14).first()
            
            if not aoi:
                print("❌ AOI 14 not found!")
                return
            
            print(f"📋 Before cleanup:")
            print(f"  Monitoring Frequency: {aoi.monitoring_frequency}")
            print(f"  Next Run At: {aoi.next_run_at}")
            print(f"  Is Active: {aoi.is_active}")
            
            # Clear the schedule completely
            aoi.monitoring_frequency = None
            aoi.next_run_at = None
            # Keep AOI active, just remove schedule
            
            session.commit()
            
            print(f"\n✅ After cleanup:")
            print(f"  Monitoring Frequency: {aoi.monitoring_frequency}")
            print(f"  Next Run At: {aoi.next_run_at}")
            print(f"  Is Active: {aoi.is_active}")
            
            print(f"\n🎉 AOI 14 schedule cleaned successfully!")
                
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

if __name__ == '__main__':
    clean_aoi_schedule()