#!/usr/bin/env python3
"""
Debug script to check schedule data in database
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from config import Config
from models import AreaOfInterest

def debug_schedule_data():
    """Check the current schedule data for AOI 14"""
    print("🔍 Debugging Schedule Data")
    print("=" * 50)
    
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    
    try:
        with db_manager.get_session() as session:
            # Get AOI 14
            aoi = session.query(AreaOfInterest).filter_by(id=14).first()
            
            if not aoi:
                print("❌ AOI 14 not found!")
                return
            
            print(f"📋 AOI 14 Details:")
            print(f"  Name: {aoi.name}")
            print(f"  Monitoring Frequency: {aoi.monitoring_frequency}")
            print(f"  Next Run At: {aoi.next_run_at}")
            print(f"  Is Active: {aoi.is_active}")
            print(f"  Created At: {aoi.created_at}")
            print(f"  Updated At: {aoi.updated_at}")
            
            # Check all AOIs with schedules
            print(f"\n📅 All AOIs with schedules:")
            all_aois = session.query(AreaOfInterest).filter(
                AreaOfInterest.next_run_at.isnot(None)
            ).all()
            
            for aoi in all_aois:
                print(f"  AOI {aoi.id}: {aoi.name} - {aoi.next_run_at} ({aoi.monitoring_frequency})")
                
            if not all_aois:
                print("  No AOIs with schedules found.")
                
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_database_update():
    """Test updating the schedule directly"""
    print(f"\n🧪 Testing Direct Database Update")
    print("=" * 50)
    
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    
    try:
        with db_manager.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(id=14).first()
            
            if not aoi:
                print("❌ AOI 14 not found!")
                return
            
            from datetime import datetime, timedelta
            
            # Set a test schedule
            old_next_run = aoi.next_run_at
            old_frequency = aoi.monitoring_frequency
            
            test_time = datetime.utcnow() + timedelta(minutes=5)
            aoi.next_run_at = test_time
            aoi.monitoring_frequency = 'test'
            
            print(f"📝 Updating schedule:")
            print(f"  Old: {old_next_run} ({old_frequency})")
            print(f"  New: {test_time} (test)")
            
            session.commit()
            print("✅ Database commit completed")
            
            # Verify the change
            session.refresh(aoi)
            print(f"📊 Verification:")
            print(f"  Current: {aoi.next_run_at} ({aoi.monitoring_frequency})")
            
            # Restore original values
            aoi.next_run_at = old_next_run  
            aoi.monitoring_frequency = old_frequency
            session.commit()
            print("🔄 Restored original values")
            
    except Exception as e:
        print(f"❌ Update test error: {e}")

if __name__ == '__main__':
    debug_schedule_data()
    test_database_update()