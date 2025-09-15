#!/usr/bin/env python3
"""
Test schedule updates by directly calling the database logic
"""
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from config import Config
from models import AreaOfInterest

def test_schedule_persistence():
    """Test if schedule changes actually persist to database"""
    print("🧪 Testing Schedule Persistence")
    print("=" * 50)
    
    db_manager = DatabaseManager(Config.DATABASE_URL, Config.SQLALCHEMY_ENGINE_OPTIONS)
    
    try:
        with db_manager.get_session() as session:
            # Get AOI 14
            aoi = session.query(AreaOfInterest).filter_by(id=14).first()
            
            if not aoi:
                print("❌ AOI 14 not found!")
                return
            
            # Show current state
            print(f"📊 Current state:")
            print(f"  Frequency: {aoi.monitoring_frequency}")
            print(f"  Next Run: {aoi.next_run_at}")
            print(f"  Active: {aoi.is_active}")
            
            # Test 1: Set a schedule for 5 minutes from now
            test_time = datetime.utcnow() + timedelta(minutes=5)
            print(f"\n🎯 Test 1: Setting schedule to {test_time}")
            
            aoi.monitoring_frequency = 'once'
            aoi.next_run_at = test_time
            aoi.is_active = True
            
            print("💾 Committing changes...")
            session.commit()
            
            # Verify immediately 
            session.refresh(aoi)
            print(f"✅ Immediate verification:")
            print(f"  Frequency: {aoi.monitoring_frequency}")
            print(f"  Next Run: {aoi.next_run_at}")
            print(f"  Match: {'✅' if aoi.next_run_at == test_time else '❌'}")
            
            # Test 2: Get a fresh session and check persistence
            print(f"\n🔍 Test 2: Fresh session check...")
            
        # New session to test persistence
        with db_manager.get_session() as fresh_session:
            fresh_aoi = fresh_session.query(AreaOfInterest).filter_by(id=14).first()
            
            print(f"📊 Fresh session state:")
            print(f"  Frequency: {fresh_aoi.monitoring_frequency}")
            print(f"  Next Run: {fresh_aoi.next_run_at}")
            print(f"  Persisted: {'✅' if fresh_aoi.next_run_at == test_time else '❌'}")
            
            if fresh_aoi.next_run_at != test_time:
                print(f"❌ PERSISTENCE ISSUE!")
                print(f"   Expected: {test_time}")
                print(f"   Got:      {fresh_aoi.next_run_at}")
                return False
            
            # Test 3: Update with new schedule
            new_test_time = datetime.utcnow() + timedelta(minutes=10)
            print(f"\n🎯 Test 3: Updating to {new_test_time}")
            
            fresh_aoi.next_run_at = new_test_time
            fresh_aoi.monitoring_frequency = 'daily'
            
            fresh_session.commit()
            fresh_session.refresh(fresh_aoi)
            
            print(f"✅ Update verification:")
            print(f"  New Next Run: {fresh_aoi.next_run_at}")
            print(f"  New Frequency: {fresh_aoi.monitoring_frequency}")
            print(f"  Match: {'✅' if fresh_aoi.next_run_at == new_test_time else '❌'}")
            
            # Clean up - restore to no schedule
            print(f"\n🧹 Cleanup...")
            fresh_aoi.monitoring_frequency = None
            fresh_aoi.next_run_at = None
            fresh_session.commit()
            
            print("✅ All tests completed!")
            return True
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_schedule_persistence()
    print(f"\n🎉 Overall result: {'SUCCESS' if success else 'FAILED'}")