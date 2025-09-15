#!/usr/bin/env python3
"""
Test timezone debugging directly via API call
"""
import requests
import json
from datetime import datetime, timedelta

# Test data - schedule for 2 hours from now
test_time = datetime.now() + timedelta(hours=2)
test_iso = test_time.isoformat() + 'Z'  # Add Z to simulate frontend

print(f"🧪 Testing timezone debugging")
print(f"Local test time: {test_time}")
print(f"ISO with Z: {test_iso}")

# Mock request data
payload = {
    "frequency": "once", 
    "scheduled_at": test_iso,
    "enabled": True
}

print(f"📡 Sending payload: {json.dumps(payload, indent=2)}")

# This would normally need auth, but let's see what the logs show
url = "http://localhost:5000/api/aoi/14/schedule-monitoring"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"📥 Response: {response.status_code}")
    print(f"📄 Body: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

print("✅ Check backend logs for timezone debugging info")