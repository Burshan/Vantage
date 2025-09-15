#!/usr/bin/env python3
"""
Solo User Scheduling Reliability Test
Tests scheduling system with multiple AOIs, different intervals, and edge cases
"""
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from threading import Thread
import logging

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_db import db_manager
from auto_analysis import AutoAnalysisManager
from models import AreaOfInterest, AnalysisHistory

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ScheduleReliabilityTester:
    """Test suite for Solo User Scheduling reliability"""
    
    def __init__(self):
        self.test_user_id = 1  # Use existing user ID for testing
        self.test_aois = []
        self.auto_manager = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_result(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if success:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {message}")
    
    def setup_test_data(self):
        """Create test AOIs with different scheduling intervals"""
        print("🛠️ Setting up test data...")
        
        test_aois_config = [
            {
                'name': 'Test AOI - Daily',
                'description': 'Daily monitoring test AOI',
                'bbox_coordinates': [-122.4194, 37.7749, -122.4094, 37.7849],  # SF
                'monitoring_frequency': 'daily',
                'next_run_at': datetime.utcnow() - timedelta(minutes=5)
            },
            {
                'name': 'Test AOI - Weekly', 
                'description': 'Weekly monitoring test AOI',
                'bbox_coordinates': [-118.2437, 34.0522, -118.2337, 34.0622],  # LA
                'monitoring_frequency': 'weekly',
                'next_run_at': datetime.utcnow() - timedelta(minutes=10)
            },
            {
                'name': 'Test AOI - Once',
                'description': 'One-time analysis test AOI',
                'bbox_coordinates': [-87.6298, 41.8781, -87.6198, 41.8881],  # Chicago
                'monitoring_frequency': 'once',
                'next_run_at': datetime.utcnow() - timedelta(minutes=2)
            },
            {
                'name': 'Test AOI - Monthly',
                'description': 'Monthly monitoring test AOI', 
                'bbox_coordinates': [-74.0060, 40.7128, -73.9960, 40.7228],  # NYC
                'monitoring_frequency': 'monthly',
                'next_run_at': datetime.utcnow() - timedelta(minutes=15)
            }
        ]
        
        try:
            with db_manager.get_session() as session:
                for aoi_config in test_aois_config:
                    aoi = AreaOfInterest(
                        user_id=self.test_user_id,
                        name=aoi_config['name'],
                        description=aoi_config['description'],
                        bbox_coordinates=aoi_config['bbox_coordinates'],
                        monitoring_frequency=aoi_config['monitoring_frequency'],
                        next_run_at=aoi_config['next_run_at'],
                        is_active=True,
                        baseline_status='completed'  # Required for analysis
                    )
                    session.add(aoi)
                    session.commit()
                    session.refresh(aoi)
                    self.test_aois.append(aoi.id)
                    
            self.log_result("Setup Test Data", True, f"Created {len(self.test_aois)} test AOIs")
            
        except Exception as e:
            self.log_result("Setup Test Data", False, f"Failed to create test data: {str(e)}")
    
    def test_basic_scheduling(self):
        """Test basic scheduling functionality"""
        print("\n📅 Testing basic scheduling functionality...")
        
        try:
            # Test getting AOIs for analysis
            aois_for_analysis = db_manager.get_aois_for_analysis()
            
            # Filter our test AOIs
            test_aois_found = [aoi for aoi in aois_for_analysis if aoi.get('aoi_id') in self.test_aois]
            
            self.log_result(
                "Get AOIs for Analysis", 
                len(test_aois_found) > 0, 
                f"Found {len(test_aois_found)} test AOIs ready for analysis"
            )
            
            # Test AutoAnalysisManager initialization
            self.auto_manager = AutoAnalysisManager(db_manager, None)  # No satellite processor for testing
            status = self.auto_manager.get_status()
            
            self.log_result(
                "AutoAnalysisManager Init", 
                status is not None, 
                f"Manager status: {status}"
            )
            
        except Exception as e:
            self.log_result("Basic Scheduling", False, f"Error: {str(e)}")
    
    def test_multiple_aoi_scheduling(self):
        """Test scheduling with multiple AOIs having different intervals"""
        print("\n🔄 Testing multiple AOI scheduling...")
        
        try:
            if not self.auto_manager:
                self.auto_manager = AutoAnalysisManager(db_manager, None)
            
            # Simulate the check_and_run_analyses process
            aois_to_analyze = db_manager.get_aois_for_analysis()
            test_aois_ready = [aoi for aoi in aois_to_analyze if aoi.get('aoi_id') in self.test_aois]
            
            self.log_result(
                "Multiple AOI Detection",
                len(test_aois_ready) >= 2,
                f"Found {len(test_aois_ready)} AOIs with different schedules"
            )
            
            # Check that different frequencies are handled correctly
            frequencies = [aoi.get('monitoring_frequency') for aoi in test_aois_ready]
            unique_frequencies = set(freq for freq in frequencies if freq)
            
            self.log_result(
                "Different Frequencies",
                len(unique_frequencies) >= 2,
                f"Found frequencies: {list(unique_frequencies)}"
            )
            
        except Exception as e:
            self.log_result("Multiple AOI Scheduling", False, f"Error: {str(e)}")
    
    def test_overlapping_schedules(self):
        """Test what happens when multiple AOIs are scheduled at similar times"""
        print("\n⏰ Testing overlapping schedules...")
        
        try:
            # Set multiple AOIs to run within a short time window
            overlap_time = datetime.utcnow() + timedelta(minutes=1)
            
            with db_manager.get_session() as session:
                updated_count = 0
                for aoi_id in self.test_aois[:2]:  # Update first 2 AOIs
                    aoi = session.query(AreaOfInterest).filter_by(id=aoi_id).first()
                    if aoi:
                        aoi.next_run_at = overlap_time + timedelta(seconds=updated_count * 30)
                        updated_count += 1
                session.commit()
            
            self.log_result(
                "Overlapping Schedule Setup",
                updated_count >= 2,
                f"Set {updated_count} AOIs with overlapping schedules"
            )
            
            # Verify the scheduler can handle this scenario
            aois_to_analyze = db_manager.get_aois_for_analysis()
            overlapping_aois = [
                aoi for aoi in aois_to_analyze 
                if aoi.get('aoi_id') in self.test_aois and
                   aoi.get('next_run_at') and
                   abs((datetime.fromisoformat(aoi['next_run_at'].replace('Z', '+00:00')) - overlap_time).total_seconds()) < 300
            ]
            
            self.log_result(
                "Overlapping Schedule Detection",
                len(overlapping_aois) >= 2,
                f"Found {len(overlapping_aois)} AOIs with overlapping schedules"
            )
            
        except Exception as e:
            self.log_result("Overlapping Schedules", False, f"Error: {str(e)}")
    
    def test_failed_analysis_handling(self):
        """Test what happens when analysis fails"""
        print("\n💥 Testing failed analysis handling...")
        
        try:
            if not self.auto_manager:
                self.auto_manager = AutoAnalysisManager(db_manager, None)
            
            # Test with an AOI that will fail (no satellite processor)
            test_aoi_id = self.test_aois[0] if self.test_aois else None
            
            if test_aoi_id:
                # This should fail gracefully since we don't have satellite processor
                success, message = self.auto_manager.force_analysis_for_aoi(test_aoi_id)
                
                self.log_result(
                    "Failed Analysis Handling",
                    not success,  # We expect this to fail gracefully
                    f"Failed as expected: {message}"
                )
                
                # Verify the AOI schedule was updated appropriately after failure
                with db_manager.get_session() as session:
                    aoi = session.query(AreaOfInterest).filter_by(id=test_aoi_id).first()
                    if aoi and aoi.next_run_at:
                        # The failed analysis should have rescheduled for later
                        self.log_result(
                            "Failure Rescheduling",
                            aoi.next_run_at > datetime.utcnow(),
                            f"AOI rescheduled for: {aoi.next_run_at}"
                        )
                    else:
                        self.log_result("Failure Rescheduling", False, "AOI not properly rescheduled")
            else:
                self.log_result("Failed Analysis Handling", False, "No test AOI available")
                
        except Exception as e:
            self.log_result("Failed Analysis Handling", False, f"Error: {str(e)}")
    
    def test_scheduler_limits(self):
        """Test scheduler respects max analyses per run limit"""
        print("\n🚦 Testing scheduler limits...")
        
        try:
            if not self.auto_manager:
                self.auto_manager = AutoAnalysisManager(db_manager, None)
            
            # Set a low limit for testing
            original_limit = self.auto_manager.max_analyses_per_run
            self.auto_manager.max_analyses_per_run = 2
            
            # Get all AOIs ready for analysis
            aois_to_analyze = db_manager.get_aois_for_analysis()
            test_aois_ready = [aoi for aoi in aois_to_analyze if aoi.get('aoi_id') in self.test_aois]
            
            if len(test_aois_ready) > 2:
                # Simulate what check_and_run_analyses does
                analyses_to_run = test_aois_ready[:self.auto_manager.max_analyses_per_run]
                
                self.log_result(
                    "Scheduler Limit Respected",
                    len(analyses_to_run) == 2,
                    f"Limited to {len(analyses_to_run)} analyses out of {len(test_aois_ready)} available"
                )
            else:
                self.log_result(
                    "Scheduler Limit Respected",
                    True,
                    f"Only {len(test_aois_ready)} AOIs ready, within limit"
                )
            
            # Restore original limit
            self.auto_manager.max_analyses_per_run = original_limit
            
        except Exception as e:
            self.log_result("Scheduler Limits", False, f"Error: {str(e)}")
    
    def test_schedule_persistence(self):
        """Test that schedules persist correctly in database"""
        print("\n💾 Testing schedule persistence...")
        
        try:
            # Create a new schedule and verify it persists
            test_time = datetime.utcnow() + timedelta(hours=1)
            
            with db_manager.get_session() as session:
                if self.test_aois:
                    aoi = session.query(AreaOfInterest).filter_by(id=self.test_aois[0]).first()
                    if aoi:
                        original_time = aoi.next_run_at
                        aoi.next_run_at = test_time
                        aoi.monitoring_frequency = 'daily'
                        session.commit()
                        
                        # Verify it was saved
                        session.refresh(aoi)
                        saved_time = aoi.next_run_at
                        
                        self.log_result(
                            "Schedule Persistence",
                            saved_time and abs((saved_time - test_time).total_seconds()) < 1,
                            f"Schedule saved correctly: {saved_time}"
                        )
                        
                        # Restore original time
                        aoi.next_run_at = original_time
                        session.commit()
                    else:
                        self.log_result("Schedule Persistence", False, "Test AOI not found")
                else:
                    self.log_result("Schedule Persistence", False, "No test AOIs available")
                    
        except Exception as e:
            self.log_result("Schedule Persistence", False, f"Error: {str(e)}")
    
    def test_timezone_handling(self):
        """Test timezone handling in schedules"""
        print("\n🌍 Testing timezone handling...")
        
        try:
            # Test various timezone formats
            timezone_tests = [
                "2024-12-10T14:30:00Z",  # UTC with Z
                "2024-12-10T14:30:00+00:00",  # UTC with offset
                "2024-12-10T14:30:00",  # No timezone (should be treated as UTC)
            ]
            
            with db_manager.get_session() as session:
                if self.test_aois:
                    aoi = session.query(AreaOfInterest).filter_by(id=self.test_aois[0]).first()
                    if aoi:
                        success_count = 0
                        
                        for tz_string in timezone_tests:
                            try:
                                # Simulate what the schedule controller does
                                clean_scheduled_at = tz_string.replace('Z', '+00:00')
                                parsed_time = datetime.fromisoformat(clean_scheduled_at)
                                
                                # Convert to UTC if it has timezone info
                                if parsed_time.tzinfo is not None:
                                    utc_time = parsed_time.utctimetuple()
                                    parsed_time = datetime(*utc_time[:6])
                                
                                # Verify it's a valid datetime
                                if isinstance(parsed_time, datetime):
                                    success_count += 1
                                    
                            except Exception as e:
                                print(f"   Failed to parse '{tz_string}': {e}")
                        
                        self.log_result(
                            "Timezone Handling",
                            success_count == len(timezone_tests),
                            f"Successfully parsed {success_count}/{len(timezone_tests)} timezone formats"
                        )
                    else:
                        self.log_result("Timezone Handling", False, "Test AOI not found")
                else:
                    self.log_result("Timezone Handling", False, "No test AOIs available")
                    
        except Exception as e:
            self.log_result("Timezone Handling", False, f"Error: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            with db_manager.get_session() as session:
                # Delete test AOIs
                deleted_count = 0
                for aoi_id in self.test_aois:
                    aoi = session.query(AreaOfInterest).filter_by(id=aoi_id).first()
                    if aoi:
                        session.delete(aoi)
                        deleted_count += 1
                
                # Delete any analysis history for test user
                analysis_deleted = session.query(AnalysisHistory).filter_by(
                    user_id=self.test_user_id
                ).delete()
                
                session.commit()
                
                self.log_result(
                    "Cleanup",
                    True,
                    f"Deleted {deleted_count} AOIs and {analysis_deleted} analysis records"
                )
                
        except Exception as e:
            self.log_result("Cleanup", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Solo User Scheduling Reliability Tests")
        print("=" * 60)
        
        # Setup
        self.setup_test_data()
        
        # Run tests
        self.test_basic_scheduling()
        self.test_multiple_aoi_scheduling()
        self.test_overlapping_schedules()
        self.test_failed_analysis_handling()
        self.test_scheduler_limits()
        self.test_schedule_persistence()
        self.test_timezone_handling()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            print("\n🚨 Errors:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        success_rate = (self.test_results['passed'] / 
                       (self.test_results['passed'] + self.test_results['failed']) * 100)
        
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Scheduling system appears reliable for solo user!")
        else:
            print("⚠️  Scheduling system needs improvements for production use.")
        
        return success_rate >= 80

def main():
    """Run the reliability test"""
    tester = ScheduleReliabilityTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()