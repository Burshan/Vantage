#!/usr/bin/env python3
"""
Complete Scheduler Fix and Test
"""
import sys
sys.path.append('.')

def complete_scheduler_fix():
    print("🔧 COMPLETE SCHEDULER DIAGNOSIS")
    print("=" * 50)
    
    # 1. Check Celery processes
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    
    worker_processes = [line for line in lines if 'celery' in line and 'worker' in line and 'grep' not in line]
    beat_processes = [line for line in lines if 'celery' in line and 'beat' in line and 'grep' not in line]
    
    print("1. 📊 Process Status:")
    print("-" * 30)
    print(f"   Celery Workers: {len(worker_processes)} running")
    print(f"   Celery Beat: {len(beat_processes)} running")
    
    # 2. Test direct task scheduling
    print("\n2. 🧪 Testing Direct Celery Task:")
    print("-" * 30)
    
    try:
        from celery_app import celery_app
        from datetime import datetime, timedelta
        
        # Test if we can connect to Celery
        i = celery_app.control.inspect()
        stats = i.stats()
        if stats:
            print("   ✅ Celery connection: OK")
        else:
            print("   ❌ Celery connection: FAILED")
            return
            
        # Schedule a simple test task for immediate execution
        from tasks import run_scheduled_analysis
        
        # Try to schedule the task to run in 30 seconds
        test_time = datetime.utcnow() + timedelta(seconds=30)
        
        # Direct Celery task scheduling
        task = run_scheduled_analysis.apply_async(
            args=[13],  # AOI 13 
            eta=test_time
        )
        
        print(f"   ✅ Direct task scheduled: {task.id}")
        print(f"   ⏰ ETA: {test_time}")
        
        # Check if task appears in scheduled queue
        scheduled = i.scheduled()
        if scheduled:
            found_task = False
            for worker, tasks in scheduled.items():
                for celery_task in tasks:
                    if celery_task.get('request', {}).get('id') == task.id:
                        print(f"   ✅ Task found in queue: {worker}")
                        found_task = True
                        break
            if not found_task:
                print(f"   ⚠️  Task not found in scheduled queue")
        
        print(f"   🕐 Wait 45 seconds and check database for new analysis...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Show what needs to be running
    print("\n3. 💡 Required Components:")
    print("-" * 30)
    print("   For scheduler to work, you need:")
    print("   ✅ Redis server (broker)")
    print("   ✅ Celery worker processes") 
    print("   ✅ Celery beat scheduler")
    print("   ✅ Flask backend (for API)")
    
    # 4. Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("   ✅ Redis: Connected")
    except Exception as e:
        print(f"   ❌ Redis: {e}")
    
    print(f"\n4. 🚀 Summary:")
    print("-" * 30)
    if len(worker_processes) > 0 and len(beat_processes) > 0:
        print("   ✅ All Celery components running")
        print("   ⏳ Direct test scheduled - check in 45 seconds")
        print("   💡 If still not working, check Celery worker logs")
    else:
        print("   ❌ Missing Celery components:")
        if len(worker_processes) == 0:
            print("      - Need to start: celery worker")
        if len(beat_processes) == 0:
            print("      - Need to start: celery beat")

if __name__ == "__main__":
    complete_scheduler_fix()