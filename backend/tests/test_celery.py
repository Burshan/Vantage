#!/usr/bin/env python3
"""
Test script for Celery task scheduling
"""
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_app import celery_app
from tasks import run_scheduled_analysis, schedule_analysis_task

def test_immediate_task():
    """Test running a task immediately"""
    print("🧪 Testing immediate task execution...")
    
    # This would run immediately (but will fail without a real AOI)
    result = run_scheduled_analysis.delay(999, 'test')  # Fake AOI ID
    
    print(f"📋 Task submitted with ID: {result.id}")
    print(f"📊 Task status: {result.status}")
    
    return result

def test_scheduled_task():
    """Test scheduling a task for the future"""
    print("🧪 Testing scheduled task...")
    
    # Schedule a task 10 seconds in the future
    future_time = datetime.utcnow() + timedelta(seconds=10)
    
    result = run_scheduled_analysis.apply_async(
        args=[999, 'test'],  # Fake AOI ID
        eta=future_time
    )
    
    print(f"⏰ Task scheduled for: {future_time}")
    print(f"📋 Task ID: {result.id}")
    
    return result

def check_redis_connection():
    """Check Redis connection and queue status"""
    print("🔍 Checking Redis connection...")
    
    import redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is connected")
        
        # Check queue length
        queue_length = r.llen('celery')
        print(f"📊 Queue length: {queue_length}")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

if __name__ == '__main__':
    print("🎯 Celery Test Suite")
    print("=" * 50)
    
    check_redis_connection()
    print()
    
    # Test immediate execution
    immediate_result = test_immediate_task()
    print()
    
    # Test scheduled execution  
    scheduled_result = test_scheduled_task()
    print()
    
    print("🎉 Tests submitted! Check the Celery worker output for results.")
    print("💡 The tasks will fail with fake AOI ID 999, but that's expected.")