#!/usr/bin/env python3
"""
Test the schedule API directly without frontend
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
AOI_ID = 14

def test_schedule_api_direct():
    """Test scheduling by calling the API directly"""
    print("🧪 Testing Schedule API Directly")
    print("=" * 50)
    
    # We can't test with authentication easily, but we can at least see the structure
    # For now, let's just test what the API expects
    
    # Test payload for 2 minutes from now
    schedule_time = datetime.now() + timedelta(minutes=2)
    
    test_payload = {
        "frequency": "once",
        "scheduled_at": schedule_time.isoformat(),
        "enabled": True
    }
    
    print(f"📤 Test payload:")
    print(json.dumps(test_payload, indent=2))
    
    print(f"\n⏰ Scheduled for: {schedule_time}")
    
    # Note: This will fail without authentication, but shows what we're sending
    try:
        response = requests.post(
            f"{BASE_URL}/api/aoi/{AOI_ID}/schedule-monitoring",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📄 Response Body: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"🔌 Request failed (expected without auth): {e}")
    
    print(f"\n📊 The issue might be:")
    print(f"  1. Frontend not sending correct data")
    print(f"  2. Backend not processing the scheduled_at correctly")
    print(f"  3. Database session issues")
    print(f"  4. Timezone conversion problems")

if __name__ == '__main__':
    test_schedule_api_direct()