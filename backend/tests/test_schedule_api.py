#!/usr/bin/env python3
"""
Test script for the schedule-monitoring API
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

# You'll need to get a real token for this test
# For now, let's just test the structure
def test_schedule_api():
    """Test the schedule API endpoints"""
    
    # Test data
    aoi_id = 14  # Using the AOI ID from your logs
    
    test_payloads = [
        # Test 1: Schedule for tomorrow
        {
            "name": "Schedule for tomorrow",
            "payload": {
                "frequency": "once",
                "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
                "enabled": True
            }
        },
        # Test 2: Weekly schedule
        {
            "name": "Weekly schedule", 
            "payload": {
                "frequency": "weekly",
                "enabled": True
            }
        },
        # Test 3: Remove schedule
        {
            "name": "Remove schedule",
            "payload": {
                "frequency": "none",
                "enabled": False
            }
        },
        # Test 4: Invalid payload (missing frequency when enabled)
        {
            "name": "Invalid - missing frequency",
            "payload": {
                "enabled": True
                # Missing frequency - should get 400
            }
        }
    ]
    
    print("🧪 Schedule API Test Scenarios")
    print("=" * 50)
    
    for test in test_payloads:
        print(f"\n📋 Testing: {test['name']}")
        print(f"📤 Payload: {json.dumps(test['payload'], indent=2)}")
        
        # Simulate what the frontend would send
        try:
            # Note: This will fail without proper auth token
            # But we can see the structure is correct
            response = requests.post(
                f"{BASE_URL}/api/aoi/{aoi_id}/schedule-monitoring",
                json=test['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            print(f"📥 Response: {response.status_code}")
            if response.text:
                try:
                    result = response.json()
                    print(f"📄 Body: {json.dumps(result, indent=2)}")
                except:
                    print(f"📄 Body: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n✅ API structure tests complete!")
    print("💡 To test with authentication, use the frontend or add proper JWT token")

if __name__ == '__main__':
    test_schedule_api()